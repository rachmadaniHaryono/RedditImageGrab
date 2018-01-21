"""views module."""
# from urllib.parse import parse_qs, urlparse
# import textwrap
import json

import humanize
from jinja2 import Markup
from flask import request, url_for
from flask_admin import AdminIndexView, expose, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_paginate import get_page_parameter, Pagination
from gallery_dl.exception import NoExtractorError
import structlog

from redditdownload import forms, models, api


log = structlog.getLogger(__name__)


def date_formatter(view, context, model, name):
    return Markup(
        '<span data-toogle="tooltip" title="{}">{}</span>'.format(
            getattr(model, name),
            humanize.naturaltime(getattr(model, name))
        )
    )


class HomeView(AdminIndexView):
    @expose('/')
    def index(self):
        form = forms.IndexForm(request.args)
        page = request.args.get(get_page_parameter(), type=int, default=1)
        subreddit = form.subreddit.data
        disable_cache = form.disable_cache.data
        template_kwargs = {'entries': None, 'subreddit': subreddit, 'form': form, }
        pagination_kwargs = {'page': page, 'show_single_page': False, 'bs_version': 3, }
        if subreddit:
            pagination_kwargs['per_page'] = 1
            url_m, res_data = api.get_url(
                subreddit, sort_mode=form.sort_mode.data, index=page, disable_cache=disable_cache)
            pagination_kwargs['total'] = res_data['total'] if res_data['total'] else 1
            instance = models.NoExtractorURL.query.filter_by(url=url_m).first()
            extracted_url_ms = []
            if not instance:
                try:
                    extracted_url_ms, extracted_url_ms_created = api.get_or_create_extracted_urls(url_m)
                    if extracted_url_ms_created and extracted_url_ms:
                        models.db.session.add_all(extracted_url_ms)
                        models.db.session.commit()
                except NoExtractorError as e:
                    log.debug('expected error', url=url_m, e=e)
                    ne_url_m = models.NoExtractorURL(url=url_m)
                    models.db.session.add(ne_url_m)
                    models.db.session.commit()
            else:
                log.debug('use cache, no extractor found', url=url_m)
            template_kwargs['entry'] = {'url': url_m, 'extracted_urls': extracted_url_ms}
        template_kwargs['pagination'] = Pagination(**pagination_kwargs)
        return self.render('redditdownload/index.html', **template_kwargs)


class URLView(BaseView):
    @expose('/')
    def index(self):
        """View for single url."""
        search_url = request.args.get('u', None)
        entry = None
        if search_url:
            entry = models.URLModel.query.filter_by(value=search_url).one_or_none()
        return self.render(
            'redditdownload/url_view.html', entry=entry, search_url=search_url)


class SearchModelView(ModelView):
    """Custom view for SearchModel model."""

    column_formatters = dict(
        created_at=date_formatter,
        subreddit=lambda v, c, m, n: Markup('<a href="{}">{}</a>'.format(
            url_for('admin.index', subreddit=m.subreddit),
            m.subreddit
        )),
    )
    can_view_details = True
    column_default_sort = ('created_at', True)
    column_exclude_list = ('after_thread_id', 'before_thread_id', )
    column_filters = ('subreddit', 'page', 'sort_mode', 'time_mode', )
    column_searchable_list = ('subreddit', 'page', )


class URLModelView(ModelView):
    """Custom view for URLModel model."""

    column_formatters = dict(
        created_at=date_formatter,
        value=lambda v, c, m, n: Markup('<a href="{0}">{0}</a>'.format(
            m.value,
        )),
    )
    can_view_details = True
    column_default_sort = ('created_at', True)
    page_size = 100


class JSONDataView(ModelView):
    """Custom view for JSONData model."""

    column_formatters = dict(
        created_at=date_formatter,
        value=lambda v, c, m, n: Markup(
            '<pre><code class="json">{}</code></pre>'.format(
                json.dumps(m.value, indent=2, sort_keys=True)
            )
        ),
    )
    extra_css = ['https://cdnjs.cloudflare.com/ajax/libs/highlight.js/9.12.0/styles/default.min.css']
    extra_js = ['https://cdnjs.cloudflare.com/ajax/libs/highlight.js/9.12.0/highlight.min.js', ]
    list_template = 'redditdownload/json_data_list.html'
