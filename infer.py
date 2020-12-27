import pandas as pd
import numpy as np
import datetime
import random
import matplotlib.pyplot as plt

time_to_death = 14  # days from exposure to death
time_to_ab = 14  # days until a surviving patient has detectable antibodies
sensitivity = 0.96
specificity = 0.99
ab_halflife = 90  # half-life of detectable antibodies in the population


class Person(object):
    """Stores data associated with simulated people"""
    def __init__(self):
        self.infected = False
        self.alive = True
        self.immune = False
        self.seropositive = False
        self.date_infected = None


def correct_seroprevalence(value):
    """Corrects for false positives and negatives"""
    return (sensitivity * value) + ((1 - specificity) * (1-value))


def simulate(parameters, deaths, plotting=False):
    """Simulates an outbreak in a sample population with fixed parameters
    parameters: tuple containing antibody half-life and case fatality rate
    deaths: dictionary mapping day numbers to death counts
    """
    ab_halflife, cfr = parameters
    print([ab_halflife, cfr])
    # infer case numbers based on later deaths
    case_counts = {}
    for i, death_count in enumerate(deaths.values()):
        if i < time_to_death:
            continue
        case_counts[list(deaths.keys())[i - time_to_death]] = int(death_count / cfr)  # infer actual number of cases
    print('percent infection: ')
    print(sum(case_counts.values()) / sample_population)
    # run simulation
    population = [Person() for i in range(sample_population)]  # generate sample population
    s = {}  # for storing seroprevalence predictions
    cutoff = np.power(0.5, 1 / ab_halflife)  # daily probability of retaining detectable antibodies
    for day in case_counts.keys():
        living = [item for item in population if item.alive is True]
        candidates = [item for item in living if item.infected is False and item.immune is False]
        seropositive = [item for item in living if item.seropositive is True]
        seropositivity_rate = len(seropositive) / len(living)
        s[day] = seropositivity_rate
        infections = case_counts[day]
        if infections < 0:
            continue  # exclude spurious negative values
        try:
            to_be_infected = random.sample(candidates, infections)  # randomly selects non-immune people to be infected
        except ValueError:
            return 1000  # return arbitrarily large value if out of candidates
        for item in to_be_infected:
            item.infected = True
            item.date_infected = day
        for item in living:
            # determine survival
            if item.infected and (item.date_infected == day - 14):
                if random.random() < cfr:  # determine survival
                    item.alive = False  # kill virtual person
                    item.infected = False
                else:
                    item.seropositive = True  # presence of antibodies
                    item.immune = True  # permanent immunity
            # determine seropositivity
            if item.seropositive:
                if random.random() < 1 - cutoff:  # determine whether person loses detectable antibodies
                    item.seropositive = False
    # calculate total error
    common_time_points = set(case_counts.keys()).intersection(serology_data.keys())
    error = 0
    for time_point in common_time_points:
        error += (s[time_point] - (correct_seroprevalence(serology_data[time_point])/sample_population))**2
    if plotting:
        plt.plot(list(case_counts.keys()), [item*sample_population for item in s.values()])
        plt.plot(list(serology_data.keys()), list(serology_data.values()))
        plt.show()
    return error

def grid_search(function, data, bounds):
    x_range = np.arange(bounds[0], bounds[1], 0.0005)
    records = {}
    minimum = 1000
    for x in x_range:
        err = function([ab_halflife, x], data)
        if err < minimum:
            minimum = err
        records[x] = err
    for x in x_range:
        if records[x] == minimum:
            return x

def grid_search_2d(function, data, bounds):
    x1_range = np.arange(bounds[0][0], bounds[0][1], 10)
    x2_range = np.arange(bounds[1][0], bounds[1][1], 0.001)
    records = {}
    minimum = 1000
    for x1 in x1_range:
        x1_record = {}
        for x2 in x2_range:
            x1_record[x2] = function([x1, x2], data)
            if x1_record[x2] < minimum:
                minimum = x1_record[x2]
        records[x1] = x1_record
    for x1 in x1_range:
        for x2 in x2_range:
            if records[x1][x2] == minimum:
                return [x1, x2]

if __name__ == '__main__':
    state = 'FL'
    serology_file = 'serology/fl_serology.csv'
    sample_population = 10000

    population_table = pd.read_csv('covid_county_population_usafacts.csv')
    county_populations = population_table.loc[population_table['State'] == state, :]
    total_population = sum(county_populations['population'])

    death_table = pd.read_csv('covid_deaths_usafacts.csv')
    date_list = death_table.columns[4:]
    state_deaths = death_table.loc[death_table['State'] == state, date_list]
    cumulative_death_counts = [sum(state_deaths[date]) for date in date_list]
    death_counts = [0]
    for i in range(1, len(cumulative_death_counts)):
        death_counts.append(cumulative_death_counts[i] - cumulative_death_counts[i-1])
    death_counts = [(item / total_population) * sample_population for item in death_counts]
    dates = [int(datetime.datetime.strptime(item, '%m/%d/%y').strftime('%j')) for item in date_list]
    #serology_data = {'04/01/2020': 0.069, '04/16/2020': 0.209, '05/06/2020': 0.232, '06/21/2020': 0.195,
    #                 '07/11/2020': 0.176, '07/30/2020': 0.184}
    serology_table = pd.read_csv(serology_file)
    serology_data = {serology_table['date'][i]: serology_table['sero'][i] for i in range(serology_table.shape[0])}
    serology_data = {int(datetime.datetime.strptime(key, '%m/%d/%y').strftime('%j')): (value/100) * sample_population for
                     key, value in sorted(serology_data.items(), key=lambda item: item[0])}

    deaths = {dates[i]: death_counts[i] for i in range(len(dates))}
    simulate([90, 0.0055], deaths, plotting=True)
    print(grid_search(simulate, deaths, (0.001, 0.01)))