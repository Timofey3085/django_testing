from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from notes.models import Note

User = get_user_model()


class TestNoteCreations(TestCase):
    NOTE_TEXT = "Текст"
    NOTE_TITLE = "Заголовок"
    NOTE_SLUG = "Slug"

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='Имя Пользователя')
        cls.url = reverse('notes:detail', args=(cls.NOTE_SLUG,))
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.form_data = {'text': cls.NOTE_TEXT,
                         'slug': cls.NOTE_SLUG,
                         'title': cls.NOTE_TITLE}

    def test_anonymous_user_cant_create_note(self):
        self.client.post(self.url, data=self.form_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_user_can_create_note(self):
        name = ('notes:add')
        name_done = ('notes:success')
        response = self.auth_client.post(reverse(name, None),
                                         data=self.form_data)
        self.assertRedirects(response, reverse(name_done, None))
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
        note = Note.objects.get()
        self.assertEqual(note.text, self.NOTE_TEXT)
        self.assertEqual(note.slug, self.NOTE_SLUG)
        self.assertEqual(note.title, self.NOTE_TITLE)
        self.assertEqual(note.author, self.user)


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

    def test_user_cant_delete_note_of_another_user(self):
        response = self.reader_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_author_can_edit_note(self):
        response = self.author_client.post(self.edit_url, data=self.form_data)
        self.assertRedirects(response, self.success_url)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.NEW_NOTE_TEXT)
        self.assertEqual(self.note.title, self.NEW_NOTE_TITLE)
        self.assertEqual(self.note.slug, self.NEW_NOTE_SLUG)

    def test_user_cant_edit_note_of_another_user(self):
        response = self.reader_client.post(self.edit_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.NOTE_TEXT)
        self.assertEqual(self.note.title, self.NOTE_TITLE)
        self.assertEqual(self.note.slug, self.NOTE_SLUG)
