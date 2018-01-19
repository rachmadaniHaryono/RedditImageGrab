"""views module."""
# from urllib.parse import parse_qs, urlparse
# import textwrap

# from flask_admin.contrib.sqla import ModelView
# from jinja2 import Markup
# import humanize
from flask import request  # , url_for
from flask_admin import AdminIndexView, expose
from flask_paginate import get_page_parameter, Pagination
from gallery_dl.exception import NoExtractorError
import structlog

from redditdownload import forms, models, api


log = structlog.getLogger(__name__)


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
