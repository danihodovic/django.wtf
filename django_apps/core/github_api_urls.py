from django.utils.http import urlencode

search_repos_by_topic_url = "https://api.github.com/search/repositories?" + urlencode(
    dict(
        q="topic:django stars:>25 pushed:>2021-06-01 is:public",
        sort="stars",
        order="desc",
        per_page=100,
    )
)

search_repos_by_keyword_url = "https://api.github.com/search/repositories?" + urlencode(
    dict(
        q="django in:readme stars:>25 pushed:>2021-06-01 is:public",
        sort="stars",
        order="desc",
        per_page=100,
    )
)
