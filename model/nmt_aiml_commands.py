#!/usr/bin/python3

import os
import sys
from subprocess import Popen
import re
import xml.etree.ElementTree as ET

aiml_txt = '../data/hello.aiml'

class Commands:
    def __init__(self):
        self.words_dupe = []
        self.text_pattern = []
        self.text_template = []
        self.text_separate = []
        self.command_string = ''
        self.text_commands = []
        self.p = None
        self.print_to_screen = True
        self.erase_history = True
        self.use_async = False

        self.setup_for_aiml()

    def setup_for_aiml(self):
        tree = ET.parse(aiml_txt)
        root = tree.getroot()
        self.text_pattern = []
        self.text_template = []

        for x in root:
            pattern = ''
            template = ''
            for y in x:
                if y.tag == 'pattern':
                    pattern = y.text.strip()
                if y.tag == 'template':
                    template = y.text.strip()
            #print(pattern, template)

            self.text_pattern.append(pattern)
            self.text_template.append(template)

        temp_pattern = []
        for x in self.text_pattern:
            x = self.re(x).lower()
            temp_pattern.append(x.split(' '))

        if self.print_to_screen: print(temp_pattern,'\n---------')

        ## remove dupes ##
        dupe_list = []
        for i in range(len(temp_pattern)):
            ii = temp_pattern[i]
            for j in range(len(ii)):
                jj = ii[j]
                for k in range(len(temp_pattern)):
                    if jj in temp_pattern[k] and k != i:
                        if jj not in dupe_list:
                            dupe_list.append(jj)

        if self.print_to_screen: print(dupe_list)
        self.words_dupe = dupe_list

        for i in range(len(temp_pattern)):
            for j in range(len(temp_pattern[i]) ,0,-1):
                j -= 1
                #print(j)
                x = temp_pattern[i][j]
                if x in dupe_list:
                    del(temp_pattern[i][j])

        if self.print_to_screen: print(temp_pattern)
        self.text_separate = temp_pattern

        for i in self.text_separate:
            for j in i:
                self.text_commands.append(j)

        if self.print_to_screen: print(self.text_commands)


    def re(self,i):
        return re.sub('[.?!:;,]','', i)

    def is_command(self,i):
        i = self.re(i)
        output = False
        for x in i.split():
            for xx in self.text_commands:
                if x.strip().lower() == xx.strip().lower():
                    output = True
        return output

    def strip_command(self,i):
        i = self.re(i)
        i = i.split()
        ii = i[:]
        for x in i:
            for xx in self.words_dupe:
                if x.strip().lower() == xx.strip().lower():
                    ii.remove(x)
        return ii


    def decide_commmand(self, i):
        self.command_string = ''

        for j in range(len(self.text_pattern)):
            if i.lower().strip().startswith(self.text_pattern[j].lower().strip()):
                self.command_string = self.text_template[j] + i[len(self.text_pattern[j]):]

        if self.print_to_screen: print(self.command_string)

        if self.command_string == '' and self.is_command(i):
            i = self.strip_command(i)
            if self.print_to_screen: print(i)
            chosen = {}
            commands = {}
            for j in range(len(self.text_separate)):
                for jj in self.text_separate[j]:
                    chosen[jj] = j
                    commands[j] = 0

            for j in i:
                for k in chosen:
                    if j.lower().strip() == k.lower().strip():
                        tot = commands[chosen[k]]
                        tot += 1
                        commands[chosen[k]] = tot

            if self.print_to_screen: print(chosen, commands)

        pass

    def do_command(self, i):
        erase = False
        self.command_string = ''
        if isinstance(i,list): i = ' '.join(i)
        i = self.re(i)

        self.decide_commmand(i)

        if self.print_to_screen: print(self.command_string)

        if not self.use_async:
            self.launch_sync(self.command_string)
        else:
            self.launch_async(self.command_string)

        if self.erase_history:
            erase = True
        return erase

    def launch_sync(self,i):
        ## if the program doesn't exist, this command will fail but chatbot will continue.
        os.system(i)
        pass

    def launch_async(self, i):
        i = i.split()
        self.p = Popen(i)
        pass

if __name__ == '__main__':
    c = Commands()


    command1 = 'movies http://youtube'
    command2 = 'play music like video music like a movie of the music band youtube.'
    command3 = 'turn around the light on'
    c.print_to_screen = True
    z = c.decide_commmand(command1)
    z = c.decide_commmand(command3)
    exit()
    for x in range(2):
        if len(c.strip_command(command1)) > 0:
            #command = c.strip_command(command)
            print(command1, x, 'here1')
            c.do_command(command1)
            exit()
        elif x is 1:
            #command = c.strip_command(command)
            print(command2, x, 'here2')
            c.do_command(command2)
            print('use previous command also.')
            pass