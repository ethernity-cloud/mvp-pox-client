#!/usr/bin/python3

with open('fileset/file1.txt') as r:
    content = r.read().title()
    print(content, 'changed version')
