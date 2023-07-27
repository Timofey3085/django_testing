import pytest

from django.urls import reverse
from django.conf import settings


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name, list',
    (('news:home', pytest.lazy_fixture('list_news')),),
)
def test_news_count(client, name, list):
    response = client.get(reverse(name))
    object_list = response.context['object_list']
    news_count = len(object_list)
    all_dates = [news.date for news in object_list]
    sorted_dates = sorted(all_dates, reverse=True)
    assert news_count == settings.NEWS_COUNT_ON_HOME_PAGE
    assert all_dates == sorted_dates


@pytest.mark.parametrize(
    'name, args, list_comments',
    (
        ('news:detail',
         pytest.lazy_fixture('slug_for_news'),
         pytest.lazy_fixture('comments')
         ),
    ),
)
def test_comments_order(client, name, args, list_comments):
    url = reverse(name, args=args)
    response = client.get(url)
    assert 'news' in response.context
    news = response.context['news']
    all_comments = news.comment_set.all()
    assert all_comments[0].created < all_comments[1].created


@pytest.mark.parametrize(
    'name, args, form',
    (
        ('news:detail',
         pytest.lazy_fixture('slug_for_news'),
         pytest.lazy_fixture('form_data')),
    ),
)
def test_anonymous_client_has_no_form(client, name, args, form):
    url = reverse(name, args=args)
    response = client.get(url)
    assert 'form' not in response.context


@pytest.mark.parametrize(
    'name, args, form, parametrized_client',
    (
        ('news:detail',
         pytest.lazy_fixture('slug_for_news'),
         pytest.lazy_fixture('form_data'),
         pytest.lazy_fixture('author_client')),
    ),
)
def test_authorized_client_has_form(client,
                                    name,
                                    args,
                                    form,
                                    parametrized_client):
    url = reverse(name, args=args)
    response = client.get(url)
    assert 'form' in response.context
