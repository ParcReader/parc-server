import arrow

from paucore.utils.python import cast_int
from simpleapi import api_export, SimpleHttpException

from catalog.article import create_article_from_api_obj, FailedToCreateArticle
from catalog.objects import ArticleApiObject
from catalog.models import Article, ARTICLE_STATUS

from .utils import api_object_from_request, api_view, pk_queryset_paginate, paginate_queryset_for_request

article_view = api_view(ArticleApiObject)


@api_export(method='POST', path=r'articles')
@article_view(collection=False)
def create_article(request):
    article_a = api_object_from_request(request, ArticleApiObject)

    try:
        article = create_article_from_api_obj(article_a)
    except FailedToCreateArticle, err:
        raise SimpleHttpException(err.message, 'article-failed-create', code=500)

    return article


@api_export(method='GET', path=r'articles')
@article_view(collection=True)
def get_articles(request):
    articles = Article.objects.all()
    since = request.GET.get('since')
    if since:
        since_date = arrow.get(since).datetime
        articles = articles.filter(updated__gte=since_date)

    articles = paginate_queryset_for_request(request, articles, pk_queryset_paginate)

    return articles


@api_export(method='GET', path=r'articles/(?P<article_id>[0-9]+)')
@article_view(collection=False)
def get_article(request, article_id):
    article_id = cast_int(article_id, None)

    try:
        article = Article.objects.get(id=article_id)
    except Article.DoesNotExist:
        raise SimpleHttpException('Article with ID does not exsits', 'missing', code=404)

    return article


@api_export(method='POST', path=r'articles/(?P<article_id>[0-9]+)')
@article_view(collection=False)
def alter_article(request, article_id):
    article_id = cast_int(article_id, None)

    try:
        article = Article.objects.get(id=article_id)
    except Article.DoesNotExist:
        raise SimpleHttpException('Article with ID does not exsits', 'missing', code=404)

    article_a = api_object_from_request(request, ArticleApiObject)

    if article.updated > article_a.date_updated:
        raise SimpleHttpException('Article on server has a more recent date_updated', 'already-updated', code=400)

    article = Article.objects.update_from_api_object(article, article_a)

    return article


def move_article_to_status(article_id, status):
    article_id = cast_int(article_id, None)

    try:
        article = Article.objects.get(id=article_id)
    except Article.DoesNotExist:
        raise SimpleHttpException('Article with ID does not exsits', 'missing', code=404)

    article.status = status
    article.save()

    return article


@api_export(method='DELETE', path=r'articles/(?P<article_id>[0-9]+)')
@article_view(collection=False)
def delete_article(request, article_id):
    return move_article_to_status(article_id, ARTICLE_STATUS.DELETED)


@api_export(method='POST', path=r'articles/(?P<article_id>[0-9]+)/archive')
@article_view(collection=False)
def archive_article(request, article_id):
    return move_article_to_status(article_id, ARTICLE_STATUS.ARCHIVED)


@api_export(method='DELETE', path=r'articles/(?P<article_id>[0-9]+)/archive')
@article_view(collection=False)
def unarchive_article(request, article_id):
    return move_article_to_status(article_id, ARTICLE_STATUS.UNREAD)
