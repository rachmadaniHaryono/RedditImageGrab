"""views module."""
import json

from flask import request, url_for, redirect, flash
from flask_admin import AdminIndexView, expose, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_paginate import get_page_parameter, Pagination
from jinja2 import Markup
import humanize
import structlog

from redditdownload import forms, models, api
from redditdownload.exception import NoAfterThreadIdError


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
        if form.subreddit.data and any(not item for key, item in request.args.items()):
            new_args = {key: value for key, value in request.args.items() if value != ''}
            return redirect(url_for('admin.index', **new_args))
        page = request.args.get(get_page_parameter(), type=int, default=1)
        template_kwargs = {'entries': None, 'form': form, }
        pagination_kwargs = {'page': page, 'show_single_page': False, 'bs_version': 3, }
        if form.subreddit.data:
            pagination_kwargs['per_page'] = 1
            try:
                search_model = api.get_search_result_on_index_page(
                    form.subreddit.data,
                    session=models.db.session,
                    page=page,
                    disable_cache=form.disable_cache.data,
                    sort_mode=form.sort_mode.data
                )
                template_kwargs['entry'] = search_model
            except NoAfterThreadIdError:
                msg = 'No after thread id found.'
                log.debug(msg)
                flash(msg, 'error')
            models.db.session.commit()
        template_kwargs['pagination'] = Pagination(**pagination_kwargs)
        return self.render('redditdownload/index.html', **template_kwargs)


class URLView(BaseView):
    @expose('/')
    def index(self):
        """View for single url."""
        form = forms.URLViewForm(request.args)
        search_url = request.args.get('u', None) or form.url.data
        if form.url.data and not search_url:
            search_url = form.url.data
        kwargs = {'form': form}
        if search_url:
            session = models.db.session
            kwargs['search_url'] = search_url
            m = models.get_or_create(session, models.URLModel, value=search_url)[0]
            if form.extract.data:
                res = api.extract_url_set_from_url_models([m], session=models.db.session)
                res = list(res)
                session.commit()
            kwargs['entry'] = m
            # url sets
            kwargs['url_sets'] = m.url_sets if m.url_sets else []
            kwargs['url_sets'].extend(m.src_url_set)
            kwargs['url_sets'].extend(m.src_url_sets)
            seen = set()
            kwargs['url_sets'] = [seen.add(obj.id) or obj for obj in kwargs['url_sets'] if obj.id not in seen]
            # kwargs['url_sets'] = list(set(kwargs['url_sets']))
            # thread models
            kwargs['thread_models'] = m.thread_models if m.thread_models else []
            kwargs['thread_models'].extend(m.permalink_thread_models)
            for url_set in kwargs['url_sets']:
                kwargs['thread_models'].extend(url_set.thread_models)
            seen = set()
            kwargs['thread_models'] = \
                [seen.add(obj.id) or obj for obj in kwargs['thread_models'] if obj.id not in seen]
            # kwargs['thread_models'] = list(set([kwargs['thread_models']]))
            # search models
            kwargs['search_models'] = []
            for thread_model in kwargs['thread_models']:
                kwargs['search_models'].extend(thread_model.search_models)
            seen = set()
            kwargs['search_models'] = \
                [seen.add(obj.id) or obj for obj in kwargs['search_models'] if obj.id not in seen]
            # kwargs['search_models'] = list(set([kwargs['search_models']]))
            models.db.session.add(m)
            models.db.session.commit()
        return self.render(
            'redditdownload/url_view.html', **kwargs)


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
