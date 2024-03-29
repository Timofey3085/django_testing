from http import HTTPStatus
from notes.forms import WARNING
from pytils.translit import slugify
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from notes.models import Note

User = get_user_model()


class TestNoteCreations(TestCase):
    NOTE_TEXT = "Текст"
    NOTE_TITLE = "Заголовок"
    NOTE_SLUG = "Slug"
    ADD_NOTE_URL = reverse('notes:add')
    NOTE_URL_SUC = reverse('notes:success')

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.url = reverse('notes:detail', args=(cls.NOTE_SLUG,))
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader = User.objects.create(username='Анон')
        cls.form_data = {'text': cls.NOTE_TEXT,
                         'slug': cls.NOTE_SLUG,
                         'title': cls.NOTE_TITLE}
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)

    def test_user_can_create_note_and_anonymous_user_cant_create_note(self):
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        for user in users_statuses:
            self.client.force_login(self.author)
            for name in ('notes:add', 'notes:success',):
                with self.subTest(user=user, name=name):
                    url = reverse(name)
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_slug_unique(self):
        self.client.force_login(self.author)
        self.client.post(self.ADD_NOTE_URL, data=self.form_data)
        response = self.client.post(self.ADD_NOTE_URL, data=self.form_data)
        Warning = self.form_data['slug'] + WARNING
        self.assertFormError(response, form='form',
                             field='slug', errors=Warning)

    def test_empy_slug(self):
        self.form_data.pop('slug')
        response = self.author_client.post(self.ADD_NOTE_URL,
                                           data=self.form_data)
        self.assertRedirects(response, self.NOTE_URL_SUC)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
        slugify_slug = slugify(self.form_data['title'])
        note_slug = Note.objects.get(slug=slugify_slug)
        self.assertEqual(slugify_slug, note_slug.slug)


class TestNoteEditDelete(TestCase):
    NOTE_TEXT = "Текст"
    NOTE_TITLE = "Заголовок"
    NOTE_SLUG = "Slug"
    NEW_NOTE_TEXT = "Новый Текст"
    NEW_NOTE_TITLE = 'Новый заголовок'
    NEW_NOTE_SLUG = 'New-Slug'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Имя Пользователя')
        cls.note = Note.objects.create(title=cls.NOTE_TITLE,
                                       text=cls.NOTE_TEXT,
                                       slug=cls.NOTE_SLUG,
                                       author=cls.author)
        cls.note_url = reverse('notes:detail', args=(cls.note.slug,))
        cls.success_url = reverse('notes:success')

        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader = User.objects.create(username='Имя Читателя')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)

        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))
        cls.form_data = {'title': cls.NEW_NOTE_TITLE,
                         'text': cls.NEW_NOTE_TEXT,
                         'slug': cls.NEW_NOTE_SLUG,
                         'author': cls.author}

    def test_author_can_delete_note(self):
        response = self.author_client.delete(self.delete_url)
        self.assertRedirects(response, self.success_url)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_author_can_edit_note(self):
        response = self.author_client.post(self.edit_url, data=self.form_data)
        self.assertRedirects(response, self.success_url)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.NEW_NOTE_TEXT)
        self.assertEqual(self.note.title, self.NEW_NOTE_TITLE)
        self.assertEqual(self.note.slug, self.NEW_NOTE_SLUG)

    def test_author_can_edit_note_and_user_cant_edit_note_another_user(self):
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),)
        for user in users_statuses:
            self.client.force_login(self.author)
            for name in ('notes:detail', 'notes:edit', 'notes:delete'):
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=(self.note.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, HTTPStatus.OK)
