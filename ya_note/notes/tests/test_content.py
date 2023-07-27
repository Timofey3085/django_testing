from django.test import TestCase
from django.urls import reverse
from notes.models import Note

from django.contrib.auth import get_user_model

User = get_user_model()


class TestHomePage(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.reader = User.objects.create(username='Читатель')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст новости',
            slug='slug',
            author=cls.author
        )
        cls.list_url = reverse('notes:list')
        cls.users = (
            (cls.author, True),
            (cls.reader, False)
        )
        cls.add_url = reverse('notes:add', args=None)
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))

    def test_notes_list_for_different_users(self):
        for user, note_in_list in self.users:
            self.client.force_login(user)
            response = self.client.get(self.list_url)
            object_list = response.context['object_list']
            self.assertEqual((self.note in object_list), note_in_list)

    def test_pages_contains_form(self):
        self.client.force_login(self.author)
        response = self.client.get(self.add_url)
        self.assertIn('form', response.context)
        response = self.client.get(self.edit_url)
        self.assertIn('form', response.context)
