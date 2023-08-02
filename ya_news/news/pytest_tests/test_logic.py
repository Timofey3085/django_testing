from http import HTTPStatus
from django.urls import reverse
from news.models import Comment
import pytest
from pytest_django.asserts import assertRedirects, assertFormError
from news.forms import BAD_WORDS, WARNING


@pytest.mark.parametrize
def test_user_can_create_note(author_client, author, form_data, slug_for_news):
    '''Тест создания заметки пользователя.'''
    url = reverse('news:detail', args=slug_for_news)
    response = author_client.post(url, data=form_data)
    assertRedirects(response, url + '#comments')
    assert Comment.objects.count() == 1
    new_comment = Comment.objects.get()
    assert new_comment.text == form_data['text']


@pytest.mark.django_db
def test_anonymous_user_cant_create_comment(client, form_data, slug_for_news):
    '''Тест создания заметки анонимного пользователя.'''
    url = reverse('news:detail', args=slug_for_news)
    response = client.post(url, data=form_data)
    login_url = reverse('users:login')
    expected_url = f'{login_url}?next={url}'
    assertRedirects(response, expected_url)
    assert Comment.objects.count() == 0


def test_user_cant_use_bad_words(author_client, form_data, slug_for_news):
    '''Тест запрета использования запрещенных слов.'''
    url = reverse('news:detail', args=slug_for_news)
    bad_words_data = {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}
    response = author_client.post(url, data=bad_words_data)
    assertFormError(
        response,
        form='form',
        field='text',
        errors=WARNING
    )
    comments_count = Comment.objects.count()
    assert comments_count == 0


def test_author_can_delete_comment(
        author_client,
        slug_for_comment,
        slug_for_news
):
    '''Тест удаления комментария автором.'''
    news_url = reverse('news:detail', args=slug_for_news)
    delete_url = reverse('news:delete', args=slug_for_comment, )
    url_to_comments = news_url + '#comments'
    response = author_client.delete(delete_url)
    assertRedirects(response, url_to_comments)
    comments_count = Comment.objects.count()
    assert comments_count == 0


def test_user_cant_delete_comment_of_another_user(
        admin_client,
        slug_for_comment
):
    '''Тест запрета удаления чужого комментария.'''
    delete_url = reverse('news:delete', args=slug_for_comment, )
    response = admin_client.delete(delete_url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comments_count = Comment.objects.count()
    assert comments_count == 1


def test_author_can_edit_comment(
        author_client,
        form_data,
        slug_for_news,
        slug_for_comment,
        comment
):
    '''Тест возможности редактировать комментарий автором.'''
    news_url = reverse('news:detail', args=slug_for_news)
    edit_url = reverse('news:edit', args=slug_for_comment, )
    url_to_comments = news_url + '#comments'
    response = author_client.post(edit_url, data=form_data)
    assertRedirects(response, url_to_comments)
    comment.refresh_from_db()
    assert comment.text == form_data['text']


def test_user_cant_edit_comment_of_another_user(
        admin_client,
        form_data,
        slug_for_comment,
        comment
):
    '''Тест запрета редактирования чужого комментария.'''
    edit_url = reverse('news:edit', args=slug_for_comment, )
    old_comment_text = comment.text
    response = admin_client.post(edit_url, data=form_data)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comment.refresh_from_db()
    assert comment.text == old_comment_text
