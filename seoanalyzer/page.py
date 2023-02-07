import hashlib
import json
import os
import re

from bs4 import BeautifulSoup
from collections import Counter
import lxml.html as lh
from string import punctuation
from urllib.parse import urlsplit
from urllib3.exceptions import HTTPError

from seoanalyzer.http import http


TOKEN_REGEX = re.compile(r'(?u)\b\w\w+\b')

class Page():
    """
    Container for each page and the core analyzer.
    """

    def __init__(self, url='', base_domain=''):
        """
        Variables go here, *not* outside of __init__
        """
        self.base_domain = urlsplit(base_domain)
        self.parsed_url = urlsplit(url)
        self.url = url
        self.title = ''
        self.description = ''
        self.keywords = {}
        self.translation = bytes.maketrans(punctuation.encode('utf-8'), str(' ' * len(punctuation)).encode('utf-8'))
        self.links = []
        self.total_word_count = 0
        self.wordcount = Counter()
        self.content_hash = None


    def talk(self):
        """
        Returns a dictionary that can be printed
        """

        context = {
            'url': self.url,
            'title': self.title,
            'word_count': self.total_word_count,
        }
        return context

    def populate(self, bs):
        """
        Populates the instance variables from BeautifulSoup
        """

        try:
            self.title = bs.title.text
        except AttributeError:
            self.title = 'No Title'

        descr = bs.findAll('meta', attrs={'name': 'description'})

        if len(descr) > 0:
            self.description = descr[0].get('content')
        keywords = bs.findAll('meta', attrs={'name': 'keywords'})

    def analyze(self, raw_html=None):
        """
        Analyze the page and populate the warnings list
        """

        if not raw_html:
            valid_prefixes = []

            # only allow http:// https:// and //
            for s in ['http://', 'https://', '//',]:
                valid_prefixes.append(self.url.startswith(s))
            try:
                page = http.get(self.url)
            except HTTPError as e:
                self.warn(f'Returned {e}')
                return
            encoding = 'ascii'

            if 'content-type' in page.headers:
                encoding = page.headers['content-type'].split('charset=')[-1]

            if encoding.lower() not in ('text/html', 'text/plain', 'utf-8'):
                # there is no unicode function in Python3
                # try:
                #     raw_html = unicode(page.read(), encoding)
                # except:
                self.warn(f'Can not read {encoding}')
                return
            else:
                raw_html = page.data.decode('utf-8')

        self.content_hash = hashlib.sha1(raw_html.encode('utf-8')).hexdigest()

        # remove comments, they screw with BeautifulSoup
        clean_html = re.sub(r'<!--.*?-->', r'', raw_html, flags=re.DOTALL)

        soup_lower = BeautifulSoup(clean_html.lower(), 'html.parser') #.encode('utf-8')
        soup_unmodified = BeautifulSoup(clean_html, 'html.parser') #.encode('utf-8')

        texts = soup_lower.findAll(text=True)
        visible_text = [w for w in filter(self.visible_tags, texts)]

        self.process_text(visible_text)
        self.populate(soup_lower)
        self.analyze_a_tags(soup_unmodified)   
        return True

    def raw_tokenize(self, rawtext):
        return TOKEN_REGEX.findall(rawtext.lower())

    def process_text(self, vt):
        page_text = ''
        for element in vt:
            if element.strip():
                page_text += element.strip().lower() + u' '
        raw_tokens = self.raw_tokenize(page_text)
        self.total_word_count = len(raw_tokens)
        
    def visible_tags(self, element):
        if element.parent.name in ['style', 'script', '[document]']:
            return False
        return True

    
    def analyze_a_tags(self, bs):
        """
        Add any new links (that we didn't find in the sitemap)
        """
        anchors = bs.find_all('a', href=True)

        for tag in anchors:
            tag_href = tag['href']
            tag_text = tag.text.lower().strip()

            if self.base_domain.netloc not in tag_href and ':' in tag_href:
                continue

            modified_url = self.rel_to_abs_url(tag_href)

            url_filename, url_file_extension = os.path.splitext(modified_url)
            # remove hash links to all urls
            if '#' in modified_url:
                modified_url = modified_url[:modified_url.rindex('#')]

            self.links.append(modified_url)

    def rel_to_abs_url(self, link):
        if ':' in link:
            return link
        relative_path = link
        domain = self.base_domain.netloc

        if domain[-1] == '/':
            domain = domain[:-1]

        if len(relative_path) > 0 and relative_path[0] == '?':
            if '?' in self.url:
                return f'{self.url[:self.url.index("?")]}{relative_path}'
            return f'{self.url}{relative_path}'

        if len(relative_path) > 0 and relative_path[0] != '/':
            relative_path = f'/{relative_path}'
        return f'{self.base_domain.scheme}://{domain}{relative_path}'

    
