import random
import numpy as np
from matplotlib import pyplot as plt

duration = 15
transmission_rate = 0.02
population = 100000
starting_immunity = 0
probability_symptomatic = 0.8


def generate_age():
    seed = random.random()
    if seed < 0.12:
        age = random.randint(0,9)
    elif seed < 0.25:
        age = random.randint(10, 19)
    elif seed < 0.64:
        age = random.randint(20, 49)
    elif seed < 0.83:
        age = random.randint(50, 65)
    else:
        age = random.randint(65, 90)
    return age


def death_probability(age):

    if age < 9:
        return 0.000016
    elif age < 19:
        return 0.0000032
    elif age < 49:
        return 0.000092
    elif age < 65:
        return 0.0014
    else:
        return 0.056


def generate_contacts(age):
    if age < 9:
        return 20
    elif age < 19:
        return 20
    elif age < 49:
        return 25
    elif age < 65:
        return 10
    else:
        return 5

class Person(object):

    def __init__(self):
        self.id = random.randint(0, 1000000000)
        self.age = generate_age()
        self.daily_contacts = generate_contacts(self.age)
        self.prob_death = death_probability(self.age)
        self.infection_length = duration
        self.alive = True
        self.dying = False
        self.infected = False
        self.quarantined = False
        self.symptomatic = False
        if random.random() < starting_immunity:
            self.immune = True
        else:
            self.immune = False
        self.days_infected = 0

    def is_alive(self):
        return self.alive

    def is_infected(self):
        return self.infected

    def is_immune(self):
        return self.immune

    def infect(self):
        if not self.immune:
            self.infected = True
            if random.random() < self.prob_death:
                self.dying = True
                self.infection_length = duration
            elif random.random() < probability_symptomatic:
                self.symptomatic = True

    def add_day(self):
        if self.infected and self.alive:
            self.days_infected += 1
        if self.days_infected == 5:
            if self.symptomatic:
                self.quarantined = True
        if self.days_infected == self.infection_length:
            if self.dying:
                self.alive = False
                self.infected = False
            else:
                self.infected = False
                self.immune = True
                self.quarantined = False


if __name__ == '__main__':
    people = [Person() for i in range(population)]
    people[0].infect()  # start outbreak
    infections = []
    immunity = []
    deaths = []
    r_0 = []
    lockdown = False
    for day in range(300):
        print(day)
        print('living population: ' + str(len([item for item in people if item.is_alive()])))
        print('infected population: ' + str(len([item for item in people if item.is_infected()])))
        infected = len([item for item in people if item.is_infected()])
        infections.append(infected)
        circulating = [item for item in people if item.is_alive() and item.quarantined is False]
        living = [item for item in people if item.is_alive()]
        print('immune population: ' + str(len([item for item in living if item.is_immune()])))
        immunity.append(len([item for item in living if item.is_immune()]) / len(living))
        deaths.append(population - len(living))
        print('')
        if infected > (population / 20):
            lockdown = True
        else:
            lockdown = False
        infection_log = {item.id: 0 for item in circulating}
        for i, item in enumerate(circulating):
            if lockdown:
                contacts = random.sample(circulating, int(item.daily_contacts / 2))
                for person in contacts:
                    if (random.random() < transmission_rate) and person.infected:
                        item.infect()
                        infection_log[person.id] += 1
            else:
                contacts = random.sample(circulating, item.daily_contacts)
                for person in contacts:
                    if (random.random() < transmission_rate) and person.infected:
                        item.infect()
                        infection_log[person.id] += 1
        temp = []
        for person in circulating:
            if person.infected:
                temp.append(infection_log[person.id])
        r_0.append(np.mean(temp))
        for item in people:
            item.add_day()
    plt.plot(infections)
    plt.show()
    plt.plot(immunity)
    plt.show()
    plt.plot(deaths)
    plt.show()
    plt.plot(r_0)
    plt.show()

    living = [item for item in people if item.is_alive()]
    immune = [item for item in living if item.is_immune()]
    sero = len(immune) / len(living)
    living_65 = [item for item in people if item.is_alive() and (item.age > 65)]
    immune_65 = [item for item in living_65 if item.is_immune()]
    sero_65 = len(immune_65) / len(living_65)
    print(sero)
    print(sero_65)
