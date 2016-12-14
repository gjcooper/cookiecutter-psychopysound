import os

projname = '{{ cookiecutter.project_short_name }}'

os.chdir(projname)
os.mkdir('data')
