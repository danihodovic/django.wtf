from datetime import datetime, timedelta

from cacheops import cached_as
from constance import config
from constance.backends.database.models import Constance

from django_wtf.core.models import Contributor, Profile, Repository, RepositoryStars

one_week_ago = datetime.today().date() - timedelta(days=7)


@cached_as(RepositoryStars, Constance, timeout=60 * 60 * 24)
def trending_repositories(**filters):
    trending = []
    for repo in Repository.valid.filter(stars__gte=20, **filters):
        stars_in_the_last_week = repo.stars_since(
            timedelta(days=config.DAYS_SINCE_TRENDING)
        )
        if stars_in_the_last_week > 0:
            setattr(repo, "stars_lately", stars_in_the_last_week)
            setattr(repo, "stars_quota", repo.stars_lately / repo.stars)  # type: ignore
            trending.append(repo)

    return sorted(trending, key=lambda e: e.stars_quota, reverse=True)


@cached_as(Contributor, timeout=60 * 60 * 24)
def most_followed_profiles():
    repos = Repository.valid.filter(stars__gte=100)
    profile_ids = (
        Contributor.objects.filter(
            contributions__gt=20,
            repository__in=repos,
            profile__followers__gt=20,
        )
        .values_list("profile__id", flat=True)
        .order_by("profile__id")
        .distinct("profile__id")
    )
    return Profile.contributes_to_valid_repos.filter(id__in=profile_ids).order_by(
        "-followers"
    )


@cached_as(Contributor, Constance, timeout=60 * 60 * 24)
def trending_profiles():
    # Contributed to a Django project
    # Sorted by most stars in the past two weeks
    trending = set()
    profiles = Profile.contributes_to_valid_repos.filter(
        contributor__contributions__gte=20,
        contributor__repository__stars__gte=20,
        followers__gte=10,
    )
    for profile in profiles:
        followers_lately = profile.followers_since(
            timedelta(days=config.DAYS_SINCE_TRENDING)
        )
        if followers_lately > 0:
            setattr(profile, "followers_lately", followers_lately)
            trending.add(profile)
    return sorted(list(trending), key=lambda e: e.followers_lately, reverse=True)
