# -*- coding: utf-8 -*-
"""Calculs de dates : semaines, grilles mensuelles, jours feries.

Tout est calcule pour l'annee demandee : changez simplement --year et les
dates suivent (y compris Paques et les jours mobiles).
"""
import datetime as dt

MON, SUN = 0, 6


# --- Utilitaires de dates -------------------------------------------------
def easter(year):
    """Dimanche de Paques (algorithme gregorien anonyme)."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(h + l - 7 * m + 114, 31)
    return dt.date(year, month, day + 1)


def nth_weekday(year, month, weekday, n):
    """n-ieme <weekday> du mois (n negatif = en partant de la fin)."""
    if n > 0:
        first = dt.date(year, month, 1)
        shift = (weekday - first.weekday()) % 7
        return first + dt.timedelta(days=shift + 7 * (n - 1))
    last_day = (dt.date(year + (month == 12), month % 12 + 1, 1) - dt.timedelta(days=1))
    shift = (last_day.weekday() - weekday) % 7
    return last_day - dt.timedelta(days=shift + 7 * (-n - 1))


def week_start_index(week_start):
    return MON if str(week_start).lower().startswith("m") else SUN


def start_of_week(day, week_start):
    ws = week_start_index(week_start)
    return day - dt.timedelta(days=(day.weekday() - ws) % 7)


def weekday_order(week_start):
    """Indices python des jours, dans l'ordre d'affichage."""
    ws = week_start_index(week_start)
    return [(ws + i) % 7 for i in range(7)]


def month_matrix(year, month, week_start):
    """Liste de semaines ; chaque semaine = 7 dates (ou None hors du mois)."""
    first = dt.date(year, month, 1)
    last = dt.date(year + (month == 12), month % 12 + 1, 1) - dt.timedelta(days=1)
    cur = start_of_week(first, week_start)
    weeks = []
    while cur <= last:
        weeks.append([(cur + dt.timedelta(days=i)) if first <= cur + dt.timedelta(days=i) <= last
                      else None for i in range(7)])
        cur += dt.timedelta(days=7)
    return weeks


def year_weeks(year, week_start):
    """Toutes les semaines couvrant l'annee (52 ou 53), sous forme de lundis."""
    cur = start_of_week(dt.date(year, 1, 1), week_start)
    end = dt.date(year, 12, 31)
    weeks = []
    while cur <= end:
        weeks.append(cur)
        cur += dt.timedelta(days=7)
    return weeks


def iso_week(day):
    return day.isocalendar()[1]


# --- Jours feries et dates notables --------------------------------------
def _fr(year):
    e = easter(year)
    d = dt.timedelta
    mothers = nth_weekday(year, 5, SUN, -1)
    if mothers == e + d(49):  # Pentecote : la fete des meres glisse en juin
        mothers = nth_weekday(year, 6, SUN, 1)
    return [
        (dt.date(year, 1, 1), "Jour de l'An", True),
        (dt.date(year, 1, 6), "Épiphanie", False),
        (dt.date(year, 2, 2), "Chandeleur", False),
        (dt.date(year, 2, 14), "Saint-Valentin", False),
        (e - d(47), "Mardi gras", False),
        (nth_weekday(year, 3, SUN, -1), "Passage heure d'été", False),
        (e, "Pâques", False),
        (e + d(1), "Lundi de Pâques", True),
        (dt.date(year, 5, 1), "Fête du Travail", True),
        (dt.date(year, 5, 8), "Victoire 1945", True),
        (e + d(39), "Ascension", True),
        (mothers, "Fête des Mères", False),
        (e + d(49), "Pentecôte", False),
        (e + d(50), "Lundi de Pentecôte", True),
        (nth_weekday(year, 6, SUN, 3), "Fête des Pères", False),
        (dt.date(year, 6, 21), "Fête de la Musique", False),
        (dt.date(year, 7, 14), "Fête nationale", True),
        (dt.date(year, 8, 15), "Assomption", True),
        (nth_weekday(year, 10, SUN, -1), "Passage heure d'hiver", False),
        (dt.date(year, 10, 31), "Halloween", False),
        (dt.date(year, 11, 1), "Toussaint", True),
        (dt.date(year, 11, 11), "Armistice 1918", True),
        (nth_weekday(year, 11, 3, 4) + d(1), "Black Friday", False),
        (dt.date(year, 12, 24), "Réveillon de Noël", False),
        (dt.date(year, 12, 25), "Noël", True),
        (dt.date(year, 12, 31), "Saint-Sylvestre", False),
    ]


def _be(year):
    e = easter(year)
    d = dt.timedelta
    return [
        (dt.date(year, 1, 1), "Nouvel An", True),
        (dt.date(year, 2, 14), "Saint-Valentin", False),
        (e - d(47), "Mardi gras", False),
        (nth_weekday(year, 3, SUN, -1), "Passage heure d'été", False),
        (e, "Pâques", False),
        (e + d(1), "Lundi de Pâques", True),
        (dt.date(year, 5, 1), "Fête du Travail", True),
        (nth_weekday(year, 5, SUN, 2), "Fête des Mères", False),
        (e + d(39), "Ascension", True),
        (e + d(49), "Pentecôte", False),
        (e + d(50), "Lundi de Pentecôte", True),
        (nth_weekday(year, 6, SUN, 2), "Fête des Pères", False),
        (dt.date(year, 7, 21), "Fête nationale", True),
        (dt.date(year, 8, 15), "Assomption", True),
        (dt.date(year, 9, 27), "Fête de la Comm. française", False),
        (nth_weekday(year, 10, SUN, -1), "Passage heure d'hiver", False),
        (dt.date(year, 10, 31), "Halloween", False),
        (dt.date(year, 11, 1), "Toussaint", True),
        (dt.date(year, 11, 11), "Armistice 1918", True),
        (dt.date(year, 12, 6), "Saint-Nicolas", False),
        (dt.date(year, 12, 25), "Noël", True),
        (dt.date(year, 12, 31), "Saint-Sylvestre", False),
    ]


def _uk(year):
    e = easter(year)
    d = dt.timedelta
    return [
        (dt.date(year, 1, 1), "New Year's Day (Bank Holiday)", True),
        (dt.date(year, 1, 2), "Bank Holiday (Scotland)", True),
        (dt.date(year, 2, 14), "Valentine's Day", False),
        (e - d(47), "Pancake Day", False),
        (e - d(21), "Mothering Sunday", False),
        (dt.date(year, 3, 17), "St Patrick's Day", False),
        (nth_weekday(year, 3, SUN, -1), "Clocks go forward", False),
        (e - d(2), "Good Friday (Bank Holiday)", True),
        (e, "Easter Sunday", False),
        (e + d(1), "Easter Monday (Bank Holiday)", True),
        (nth_weekday(year, 5, MON, 1), "Early May Bank Holiday", True),
        (nth_weekday(year, 5, MON, -1), "Spring Bank Holiday", True),
        (nth_weekday(year, 6, SUN, 3), "Father's Day", False),
        (nth_weekday(year, 8, MON, 1), "Summer Bank Holiday (Scotland)", True),
        (nth_weekday(year, 8, MON, -1), "Summer Bank Holiday", True),
        (nth_weekday(year, 10, SUN, -1), "Clocks go back", False),
        (dt.date(year, 10, 31), "Halloween", False),
        (dt.date(year, 11, 5), "Bonfire Night", False),
        (nth_weekday(year, 11, SUN, 2), "Remembrance Sunday", False),
        (nth_weekday(year, 11, 3, 4) + d(1), "Black Friday", False),
        (dt.date(year, 12, 25), "Christmas Day", True),
        (dt.date(year, 12, 26), "Boxing Day", True),
        (dt.date(year, 12, 31), "New Year's Eve", False),
    ]


def _us(year):
    e = easter(year)
    d = dt.timedelta
    return [
        (dt.date(year, 1, 1), "New Year's Day", True),
        (nth_weekday(year, 1, MON, 3), "Martin Luther King Jr. Day", True),
        (dt.date(year, 2, 2), "Groundhog Day", False),
        (dt.date(year, 2, 14), "Valentine's Day", False),
        (nth_weekday(year, 2, MON, 3), "Presidents' Day", True),
        (nth_weekday(year, 3, SUN, 2), "Daylight Saving starts", False),
        (dt.date(year, 3, 17), "St Patrick's Day", False),
        (e, "Easter Sunday", False),
        (dt.date(year, 4, 15), "Tax Day", False),
        (dt.date(year, 5, 5), "Cinco de Mayo", False),
        (nth_weekday(year, 5, SUN, 2), "Mother's Day", False),
        (nth_weekday(year, 5, MON, -1), "Memorial Day", True),
        (dt.date(year, 6, 14), "Flag Day", False),
        (nth_weekday(year, 6, SUN, 3), "Father's Day", False),
        (dt.date(year, 6, 19), "Juneteenth", True),
        (dt.date(year, 7, 4), "Independence Day", True),
        (nth_weekday(year, 9, MON, 1), "Labor Day", True),
        (nth_weekday(year, 10, MON, 2), "Indigenous Peoples' Day", True),
        (dt.date(year, 10, 31), "Halloween", False),
        (dt.date(year, 11, 1), "Daylight Saving ends", False),
        (dt.date(year, 11, 11), "Veterans Day", True),
        (nth_weekday(year, 11, 3, 4), "Thanksgiving", True),
        (nth_weekday(year, 11, 3, 4) + d(1), "Black Friday", False),
        (dt.date(year, 12, 24), "Christmas Eve", False),
        (dt.date(year, 12, 25), "Christmas Day", True),
        (dt.date(year, 12, 31), "New Year's Eve", False),
    ]


REGIONS = {"FR": _fr, "BE": _be, "UK": _uk, "US": _us}


def region_dates(code, year):
    """[(date, libelle, ferie?)] triees, pour la region demandee."""
    items = REGIONS[code](year)
    if code == "US":  # DST end = 1er dimanche de novembre
        items = [(nth_weekday(year, 11, SUN, 1), lbl, f) if lbl == "Daylight Saving ends"
                 else (d_, lbl, f) for d_, lbl, f in items]
    return sorted(items, key=lambda x: x[0])
