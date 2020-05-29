#!/usr/bin/python3

f = open('fileset/file1.txt')
content = f.read().title()
f.close()

print(content)
