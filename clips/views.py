import datetime
import os
import json

from dateutil import relativedelta
from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.shortcuts import render
from django.utils import timezone

from .models import Clip, Game, TwitchSettings
from .utils import matchGameToClip


class globalConf():
    # change these according to your language
    headline_top_week = "🔥 Top clips of the week"
    headline_top_month = "🤩 Top clips of the month"
    headline_top_alltime = "🏆 All time favorites"
    headline_search = "🔍 Search results"
    headline_stats = "📈 Statistics"
    sort_options = {
        "Views ascending": "view_count",
        "Views descending": "-view_count",
        "Date ascending": "created_at",
        "Date descending": "-created_at"
    }


def index(request):
    broadcaster_name = TwitchSettings.objects.all().get().broadcaster_name
    games = Game.objects.all()
    last_week = datetime.datetime.now() - datetime.timedelta(weeks=1)
    last_month = datetime.datetime.now() - datetime.timedelta(weeks=4)

    clips_top_week = Clip.objects.filter(
        created_at__gte=last_week).order_by("-view_count")[:8]
    clips_top_month = Clip.objects.filter(
        created_at__gte=last_month).order_by("-view_count")[:8]
    clips_top_alltime = Clip.objects.order_by("-view_count")[:8]

    matchGameToClip(clips_top_week)
    matchGameToClip(clips_top_month)
    matchGameToClip(clips_top_alltime)

    context = {"clips_top_week": clips_top_week,
               "clips_top_month": clips_top_month,
               "clips_top_alltime": clips_top_alltime,
               "games": games,
               "headline": broadcaster_name + " Clip Archive",
               "headline_top_week": globalConf().headline_top_week,
               "headline_top_month": globalConf().headline_top_month,
               "headline_top_alltime": globalConf().headline_top_alltime,
               "broadcaster_name": broadcaster_name,
               "sort_options": globalConf().sort_options
               }

    return render(request, "clips/index.html", context)


def topweek(request):
    broadcaster_name = TwitchSettings.objects.all().get().broadcaster_name
    games = Game.objects.all()
    last_week = datetime.datetime.now() - datetime.timedelta(weeks=1)

    clips_top_week = Clip.objects.filter(
        created_at__gte=last_week).order_by("-view_count")

    matchGameToClip(clips_top_week)

    # Pageination
    paginator = Paginator(clips_top_week, 30)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {"page_obj": page_obj,
               "clips": clips_top_week,
               "games": games,
               "headline": globalConf().headline_top_week,
               "broadcaster_name": broadcaster_name,
               "sort_options": globalConf().sort_options
               }

    return render(request, "clips/top-x.html", context)


def topmonth(request):
    broadcaster_name = TwitchSettings.objects.all().get().broadcaster_name
    games = Game.objects.all()
    last_month = datetime.datetime.now() - datetime.timedelta(weeks=4)

    clips_top_month = Clip.objects.filter(
        created_at__gte=last_month).order_by("-view_count")

    matchGameToClip(clips_top_month)

    # Pageination
    paginator = Paginator(clips_top_month, 30)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {"page_obj": page_obj,
               "clips": clips_top_month,
               "games": games,
               "headline": globalConf().headline_top_month,
               "broadcaster_name": broadcaster_name,
               "sort_options": globalConf().sort_options
               }

    return render(request, "clips/top-x.html", context)


def topalltime(request):
    broadcaster_name = TwitchSettings.objects.all().get().broadcaster_name
    games = Game.objects.all()
    clips_top_alltime = Clip.objects.order_by("-view_count")

    matchGameToClip(clips_top_alltime)

    # Pageination
    paginator = Paginator(clips_top_alltime, 30)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {"page_obj": page_obj,
               "clips": clips_top_alltime,
               "games": games,
               "headline": globalConf().headline_top_alltime,
               "broadcaster_name": broadcaster_name,
               "sort_options": globalConf().sort_options
               }

    return render(request, "clips/top-x.html", context)


def search(request):
    broadcaster_name = TwitchSettings.objects.all().get().broadcaster_name
    games = Game.objects.all()
    search = request.GET.get("search")
    sort = request.GET.get("sort")
    searchgame = request.GET.get("game")

    if searchgame:
        game_id = Game.objects.filter(name=searchgame).get().game_id
        object_list = Clip.objects.filter(
            Q(title__icontains=search) & Q(game_id__icontains=game_id) | Q(creator_name__icontains=search) & Q(
                game_id__icontains=game_id) | Q(clip_id__icontains=search) & Q(game_id__icontains=game_id))
    else:
        object_list = Clip.objects.filter(
            Q(title__icontains=search) | Q(creator_name__icontains=search) | Q(clip_id__icontains=search))

    if sort in globalConf().sort_options:
        object_list = object_list.order_by(globalConf().sort_options[sort])
    else:
        object_list = object_list.order_by("-view_count")

    matchGameToClip(object_list)

    # Pageination
    paginator = Paginator(object_list, 30)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {"page_obj": page_obj,
               "clips": object_list,
               "games": games,
               "headline": globalConf().headline_search,
               "results": len(object_list),
               "broadcaster_name": broadcaster_name,
               "sort_options": globalConf().sort_options
               }

    context["query"] = str("?sort=" + sort + "&game=" +
                           searchgame + "&search=" + search).replace(" ", "+")

    return render(request, "clips/search.html", context)


def statistics(request):
    broadcaster_name = TwitchSettings.objects.all().get().broadcaster_name
    games = Game.objects.all()

    # most clips by user
    most_clips_by_user = Clip.objects.values("creator_name").annotate(
        amount=Count("creator_name")).order_by("-amount")[:10]

    # most total views by user
    most_views_by_user = Clip.objects.values("creator_name").annotate(
        amount=Sum("view_count")).order_by("-amount")[:10]

    # clips per month chart
    clips_in_month = {
        "datasets": [{
            "data": [],
            "borderWidth": 2,
            "borderColor": "rgba(255,255,255,1)"
        }],
        "labels": []
    }
    for i in range(5, -1, -1):
        first_day_of_month = timezone.now().date().replace(
            day=1) - relativedelta.relativedelta(months=i)
        amount = Clip.objects.filter(
            created_at__range=[first_day_of_month, first_day_of_month + relativedelta.relativedelta(months=1)]).count()
        month = (timezone.now() -
                 relativedelta.relativedelta(months=i)).strftime("%B")

        clips_in_month["datasets"][0]["data"].append(amount)
        clips_in_month["labels"].append(month)

    # most clips by category chart
    clips_by_category = {
        "datasets": [{
            "data": [],
            "borderWidth": 2,
            "borderColor": "rgba(255,255,255,1)"
        }],
        "labels": []
    }
    most_clips_by_category = Clip.objects.values("game_id").annotate(
        amount=Count("game_id")).order_by("-amount")[:10]

    for category in most_clips_by_category:
        game_title = Game.objects.filter(
            game_id__icontains=category["game_id"]).get().name
        category.pop("game_id", None)
        clips_by_category["datasets"][0]["data"].append(category["amount"])
        clips_by_category["labels"].append(game_title)

    context = {
        "broadcaster_name": broadcaster_name,
        "headline": globalConf().headline_stats,
        "games": games,
        "sort_options": globalConf().sort_options,
        "most_clips_by_user": most_clips_by_user,
        "most_views_by_user": most_views_by_user,
        "clips_in_month": json.dumps(clips_in_month),
        "clips_by_category": json.dumps(clips_by_category)
    }

    return render(request, "clips/stats.html", context)
