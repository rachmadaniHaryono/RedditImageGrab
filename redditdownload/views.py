"""views module."""
import json

from flask import request, url_for, redirect
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
        if form.subreddit.data and any(not item for key, item in request.args.items()):
            new_args = {key: value for key, value in request.args.items() if value != ''}
            return redirect(url_for('admin.index', **new_args))
        page = request.args.get(get_page_parameter(), type=int, default=1)
        template_kwargs = {'entries': None, 'form': form, }
        pagination_kwargs = {'page': page, 'show_single_page': False, 'bs_version': 3, }
        if form.subreddit.data:
            pagination_kwargs['per_page'] = 1
            search_model = api.get_search_result_on_index_page(
                form.subreddit.data,
                session=models.db.session,
                page=page,
                disable_cache=form.disable_cache.data,
                sort_mode=form.sort_mode.data
            )
            models.db.session.commit()
            template_kwargs['entry'] = search_model
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
            kwargs['search_url'] = search_url
            if form.extract.data:
                pass
            else:
                entry = models.URLModel.query.filter_by(value=search_url).one_or_none()
                kwargs['entry'] = entry
                if entry is not None:
                    kwargs['json_data_list'] = \
                        [json.dumps(x.value, indent=2, sort_keys=True) for x in entry.json_data_list]
                else:
                    kwargs['json_data_list'] = None
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
