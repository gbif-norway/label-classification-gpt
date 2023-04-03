import re
from typing import List
import pickle
import pycountry
import psycopg2
import os
from dateutil.parser import parse


def lines(text):
    return re.split('\n', text)

def get_connection():
   return psycopg2.connect(
      dbname=os.environ["DO_PG_DB"],
      user=os.environ["DO_PG_USER"],
      password=os.environ["DO_PG_PASSWORD"],
      host=os.environ["DO_PG_URI"],
      port=os.environ["DO_PG_PORT"]
  )

def exact_search(candidate, table, column, additional_where=''):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT {column} FROM {table} WHERE {column} = '{candidate}' {additional_where} LIMIT 1;")
            exact_match = cursor.fetchone()
            if exact_match:
                print(f'Found exact match for {candidate} in {table}:{column}')
                return exact_match[0]
    return None

def max_distance(word):
    word_length = len(word)
    if word_length <= 9:
        return 1
    elif word_length <= 12:
        return 2
    else:
        return 3
    
def max_distance_fuzzier(word):
    word_length = len(word)
    if word_length <= 3:
        return 1
    if word_length <= 6:
        return 2
    if word_length <= 9:
        return 3
    elif word_length <= 12:
        return 4
    else:
        return 5

def fuzzy_search(candidate, table, column, max_distance, additional_where=''):
    if len(candidate) < 3:
        return (None, None)
    print(f'Doing fuzzy search for {candidate} in {column} with {additional_where}')
    with get_connection() as connection:
        with connection.cursor() as cursor:
            sql = f"""
                SELECT {column}, levenshtein({column}, '{candidate}') AS distance
                FROM {table}
                WHERE levenshtein({column}, '{candidate}') <= {max_distance}
                {additional_where}
                ORDER BY distance ASC
                LIMIT 3;
            """
            cursor.execute(sql)

            matches = cursor.fetchall()
            if matches:
                #print(f"Top 3 matches within allowed distance:")
                #for match in matches:
                #    print(f"{match[0]} (distance: {match[1]})")
                return matches[0]
            #else:
            #    print(f'No matches within allowed distance found for {candidate} with distance {max_distance(len(candidate))}.')
    return (None, None)

def scientific_name(full):
    #print('-----Searching taxa-----')
    words = _get_latin_words_for_search(full)
    genus = None

    for genus_idx, word in enumerate(words):
        genus = exact_search(word, table='distinct_genus', column='genus')
        if genus:
            break

    if not genus:
        min_distance = 9999
        for i, word in enumerate(words):
            candidate, distance = fuzzy_search(word, table='distinct_genus', column='genus', max_distance=max_distance(word))
            if candidate and distance <= min_distance:
                genus = candidate
                min_distance = distance
                genus_idx = i

    if not genus:  # Can't find genus, try to find a family
        for word in words:
            family = exact_search(word, table='distinct_family', column='family')
            if family:
                return family
            
        family = None
        for word in words:
            candidate, distance = (fuzzy_search(word, table='distinct_family', column='family', max_distance=max_distance(word)))
            if candidate and distance <= min_distance:
                family = candidate
        return family 

    try:
        epithet_candidate = words[genus_idx + 1]
    except IndexError:  # There is no subsequent word in the OCR
        return genus 
    
    where = f"AND genus = '{genus}'"
    epithet = exact_search(epithet_candidate, table='taxonomy', column='infraspecificepithet', additional_where=where)
    if not epithet:
        epithet, distance = fuzzy_search(epithet_candidate, table='taxonomy', column='infraspecificepithet', additional_where=where, max_distance=max_distance_fuzzier(word))
    if epithet:
        return f'{genus} {epithet}'
    return genus

def elevation(full):
    lines = re.split('\n', full)
    numbers = r'([1-9][0-9]{2,3}(-[1-9][0-9]{2,3})?)'
    units = r'([mм]|ft)'
    non_digit_la = r'(?!\d)'
    non_digit_lb = r'(?<!\d)'
    prefix = r'(alt|h|altitude|height|Высотанадуровнемморя)[\-\.:]*' # Высота над уровнем моря = Height above sea level

    for line in lines:
        unspaced_line = line.replace(' ', '')

        matches = re.search(f'{prefix}({numbers}{units}?){non_digit_la}', unspaced_line, re.IGNORECASE|re.UNICODE)
        if matches:
            return matches.group(2)
        
        matches = re.search(f'{prefix}{numbers}{non_digit_la}', unspaced_line, re.IGNORECASE|re.UNICODE)
        if matches:
            return matches.group(2)
        
        matches = re.search(f'[\n\s]+{numbers}\s*{units}', line, re.IGNORECASE|re.UNICODE)
        if matches:
            return matches.group(0).replace(' ', '')

        matches = re.search(f'[24][-:]+({numbers}{units}?){non_digit_la}', unspaced_line, re.IGNORECASE|re.UNICODE)
        if matches:
            return matches.group(1)
    
    unspaced = ''.join([l.replace(' ', '') for l in lines])

    matches = re.search(f'{prefix}({numbers}{units}?){non_digit_la}', unspaced, re.IGNORECASE|re.UNICODE)
    if matches:
        return matches.group(2)

    # matches = re.search(f'{non_digit_lb}({numbers}{units}?){prefix}', unspaced, re.IGNORECASE|re.UNICODE)
    # if matches:
    #     return matches.group(1)

    return None

def min_max_elevation_in_meters(text):  # Has spaces stripped
    if not text:
        return None, None
    number_matches = re.findall('[1-9][0-9]{2,3}', text)
    max = number_matches.pop() 
    min = number_matches.pop() if number_matches else max
    units = re.search('([mм]|ft)', text)
    if units and units.group(0) == 'ft':
        min = round(int(min) / 3.281)
        max = round(int(max) / 3.281)
    return str(min), str(max)

def record_number(lines):
    for line in lines:
        matches = re.search('(no|№)[\.\s\:]*(\d+)', line, re.IGNORECASE|re.UNICODE)
        if matches:
            return matches.group(2)
    return None

def date(full):
    lines = re.split('\n', full)
    # for line in lines:
    #     try:
    #         date = parse(line, fuzzy=True)
    #         return date.strftime('%Y-%m-%d')
    #     except Exception as e:
    #         pass
    for line in lines:
        matches = re.search('[\s\:\.]?((1[789][0-9]|20[012])\d)', line)
        if matches:
            return matches.group(1).replace(':', '').replace('.', '').replace(' ', '')
    return None

def names_known_collectors(full, countrycode):
    #print('-----Searching people-----')
    candidates = [x.lower() for x in _get_latin_words_for_search(full) if len(x) > 4]
    found_names = []
    for candidate in candidates:
        name = exact_search(candidate, table='people', column='person_name')
        if name:
            found_names.append(name)
    for candidate in candidates:
        if candidate not in found_names:
            where = f" AND countrycode='{countrycode}'" if countrycode else None
            name, distance = fuzzy_search(candidate, table='people', column='person_name', additional_where=where, max_distance=max_distance(candidate))
            if name:
                found_names.append(name)
    return [x.title() for x in found_names]

def names_from_prefix(lines):
    for line in lines:
        collected = ['collected', 'coll.', 'coll:', 'collector']
        for phrase in collected:
            matches = re.search(phrase, line, re.IGNORECASE)
            if matches:
                return line.split(matches.group(0))[-1].strip()
    return []

def names_from_nltk(full):
    pass

def country(lines):
    for line in lines:
        common_countries = ['Tajikistan', 'Afghanistan', 'China', 'Russia', 'Kazakhstan', 'Italy', 'Norway', 'Armenia']
        for country in common_countries:
            if country.lower() in line.lower():
                return country
        
        for country in pycountry.countries:
            if country.name.lower() in line.lower():
                return country.name

def _get_latin_words_for_search(full: str) -> List[str]:
    full = ' '.join(re.split('\n', full))
    only_words = re.sub('[^A-Za-z()\s\-]', '', full)
    stripped_spaces = re.sub('\s+', ' ', only_words)
    return [x for x in re.split('\s', stripped_spaces.strip()) if len(x) > 3]
