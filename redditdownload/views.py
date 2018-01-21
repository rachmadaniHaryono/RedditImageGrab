"""views module."""
# from urllib.parse import parse_qs, urlparse
# import textwrap
import json

from flask import request, url_for
from flask_admin import AdminIndexView, expose, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_paginate import get_page_parameter, Pagination
from jinja2 import Markup
import humanize
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
        sort_mode = None
        template_kwargs = {'entries': None, 'subreddit': subreddit, 'form': form, }
        pagination_kwargs = {'page': page, 'show_single_page': False, 'bs_version': 3, }
        if subreddit:
            pagination_kwargs['per_page'] = 1
            search_m, search_m_created = api.get_or_create_search_model(
                subreddit, sort_mode=sort_mode, disable_cache=disable_cache, page=page)
            if search_m_created:
                models.db.session.add(search_m)
                models.db.session.commit()
            url_set_list = []
            url_ms = list(api.filter_url_models([x.url for x in search_m.thread_models]))
            for url_m in url_ms:
                url_set_list.append(api.get_or_create_url_set(url_m))
            if any(x[1] for x in url_set_list):
                models.db.session.add_all([x[0] for x in url_set_list])
                models.db.session.commit()
            template_kwargs['entries'] = [x[0] for x in url_set_list]
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
