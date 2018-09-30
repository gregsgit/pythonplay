#!/usr/bin/env python3

import re
import sys
import datetime

field_num_dict = {}  # map field_name (lower case) to field number in line

# counties_by_day maps a given County Code to a 365-element list.
# Each element in the list is a dictionary keyed by species Common Name.
# Each element in the dictionary for a day is the average number of individuals
# reported for that day for that species for that county, when there was a non-zero
# report for that species on that day and location.
# Ex: counties_by_day["US-AR-143"][day_of_year_from_mmdd("5/11")]["Wilson's Warbler"]
#   returns the averarge number of Wilson's Warblers reported on the 130th day of the 
#   year for county with ID "US-AR-143", because day_of_year_from_mmdd("5/11") returns 130, 

counties_by_day = {}
counties_by_day_working = {}  # same structure but maps to (sum, count) 

# takes strings of form "mm/dd", "m/dd", "mm/d", "m/d" and converts to
# number between 0 and 364. We ignore 12/31 in leap years, which would be 366. 
def day_of_year_from_mmdd(str):
    # use 2018 for year - not a leap year
    doy = datetime.datetime.strptime(str+"/2018", "%m/%d/%Y").timetuple().tm_yday
    # print("{} is {} day of year.".format(str, doy))
    return doy - 1

# 0-based day of year from "yyyy-mm-dd"
def day_of_year_from_yyyymmdd(str):
    doy = datetime.datetime.strptime(str, "%Y-%m-%d").timetuple().tm_yday
    # print("{} is {} day of year.".format(str, doy))
    return doy - 1

# field num, given field name
def fnum(str):
    return field_num_dict[str.lower().strip()]

# assuming 'line' is list of field from first line of TSV file,
# populate global 'field_nums' dictionary with mapping from
# lower case field name to index (starting at 0)
def line1_to_field_nums(line):
    line_fields = line.rstrip().split('\t') # split into fields using tab separators
    i = 0
    for field in line_fields:
        field_num_dict[field.lower().strip()] = i
        print("{} -> {}".format(field.lower().strip(), i))
        i += 1

with open("temp.txt", encoding="utf8") as f:
    line_num = 0
    for line in f:
        line_num += 1
        new_entry = False
        if line_num == 1:
            line1_to_field_nums(line)
            continue            # go to next line

        # print("\n**** LINE: {} ***".format(line_num))
        line_fields = line.rstrip().split('\t') # split into fields using tab separators

        # print("\t Date: {}, Common Name: {}, County Code: {}, Count: {}.".
        #       format(line_fields[fnum('Observation Date')], line_fields[fnum('Common Name')], 
        #              line_fields[fnum('County Code')], line_fields[fnum('Observation Count')]))

        county_id = line_fields[fnum('County Code')]
        obs_date = line_fields[fnum('Observation Date')]
        doy = day_of_year_from_yyyymmdd(obs_date)
        species = line_fields[fnum('Common Name')]
        obs_count_str = line_fields[fnum('Observation Count')]

        if obs_count_str == 'X':
            print("Got observation count of 'X'")
            continue            # nothing to do here

        if not county_id:
            print("Got blank county_id")
            continue

        obs_count = int(obs_count_str)

        if county_id not in counties_by_day:
            counties_by_day[county_id] = [{} for x in range(366)]
            counties_by_day_working[county_id] = [{} for x in range(366)]
            
        # get dictionaries keyed by species for this day in this county:
        county_day_dict = counties_by_day[county_id][doy]
        county_day_working_dict = counties_by_day_working[county_id][doy]
        
        # initialize dictionary entries for this species
        if species not in county_day_working_dict:
            new_entry = True
            county_day_working_dict[species] = (0,0)

        # update working numbers:
        (sum, numdays) = county_day_working_dict[species]
        sum += obs_count
        numdays += 1
        county_day_working_dict[species] = (sum, numdays)
        
        # update running average:
        ave = sum / numdays
        county_day_dict[species] = ave

        if not new_entry:
            print("Updated ave: {}, for {} at {} on doy {} (from {})".
                  format(ave, species, county_id, doy, obs_date))

        if line_num > 1000:
            break
