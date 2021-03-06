from flask import render_template, request, redirect, url_for, current_app
from pprint import pprint
from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import Graph, plugin, URIRef, Literal
from rdflib.parser import Parser
from rdflib.serializer import Serializer
import json
import re

from . import main


@main.route('/index.html', methods=['GET', 'POST'])
@main.route('/viewer.html', methods=['GET', 'POST'])
@main.route('/viewer', methods=['GET', 'POST'])
@main.route('/', methods=['GET', 'POST'])
def all_worksets():
    user = request.args.get('user', '') or '"Demo user"'
    worksets = select_worksets(specific_user = "BIND({0} as ?username)".format(user))
    return render_template("viewer.html", worksets = worksets, user = user)

@main.route('/view_workset', methods=['GET'])
def detail_workset():
    workseturi = request.args.get('uri', '')
    ws = "BIND(<{0}> as ?workset) .".format(workseturi)
    workset = select_worksets(ws)
    return render_template("workset.html", worksets=workset)

def select_worksets(specific_workset = "", specific_user = ""):
    app = current_app._get_current_object()
    sparql = SPARQLWrapper(endpoint = app.config["ENDPOINT"]) 
    sparql.setCredentials(user = app.config["SPARQLUSER"], passwd = app.config["SPARQLPASSWORD"])
    selectWorksetsQuery = open(app.config["ELEPHANT_QUERY_DIR"] + "select_worksets.rq").read()
    query = selectWorksetsQuery.format(specific_workset, specific_user)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    try: 
       results = sparql.query().convert()
    except: 
       return {};
    worksets = dict()
    for result in results["results"]["bindings"]:
        if result["workset"]["value"] not in worksets:
            worksets[result["workset"]["value"]] = {
                "uri": result["workset"]["value"],
                "mod_date": result["mod_date"]["value"],
                "title": result["title"]["value"],
                "abstract": result["abstract"]["value"],
                "user": result["username"]["value"],
                "works": list()
            }
        if (result["saltset"]["value"] == "http://eeboo.oerc.ox.ac.uk/saltsets/htrc-wcsa_works"): 
            saltset = "htrc-wcsa_works"
        else:
            saltset = "eeboo_works"
	try:
  	    worksets[result["workset"]["value"]]["works"].append(
	    {
		"uri": result["work"]["value"], 
		"worktitle": result["worktitle"]["value"],
		"author": result["author"]["value"],
		"creator": result["creator"]["value"],
		"pubdate": result["pubdate"]["value"].replace("-01-01",""), #FIXME
		"datePrecision": result["datePrecision"]["value"],
		"place": result["place"]["value"],
#                "imprint": result["imprint"]["value"],
		"elecLoc": result["elecLoc"]["value"],
		"viaf": result["viaf"]["value"],
		"loc": result["loc"]["value"],
		"saltset":saltset
	    })
	except:
	    # FIXME unicode issue 
	    pass
    for workset in worksets:
        worksets[workset]["works"] = sorted(worksets[workset]["works"], key=lambda k: (k["author"], k["worktitle"]))
    return worksets

@main.route('/construct.html', methods = ['GET', 'POST'])
@main.route('/construct', methods = ['GET', 'POST'])
def construct_workset():
    app = current_app._get_current_object()
    sparql = SPARQLWrapper(app.config["ENDPOINT"])
    sparql.setCredentials(user = app.config["SPARQLUSER"], passwd = app.config["SPARQLPASSWORD"])
    # Get a list of all eeboo persons plus all HTRC persons who are NOT aligned to eeboo persons
    selectPersonsQuery = open(app.config["ELEPHANT_QUERY_DIR"] + "select_persons.rq").read()
    sparql.setQuery(selectPersonsQuery)
    sparql.setReturnFormat(JSON)
    personResults = sparql.query().convert()
    persons = list()
    for p in personResults["results"]["bindings"]:
        persons.append({ "uri": p["uri"]["value"], "label": p["label"]["value"] })
    # Get a list of all place names, distinct among both datasets
    selectPlacesQuery = open(app.config["ELEPHANT_QUERY_DIR"] + "select_places.rq").read()
    sparql.setQuery(selectPlacesQuery)
    placeResults = sparql.query().convert()
    places = list()
    for p in placeResults["results"]["bindings"]:
        places.append(p["place"]["value"])
    # Get a list of all subject strings in HTRC
    selectSubjectsQuery = open(app.config["ELEPHANT_QUERY_DIR"] + "select_subjects.rq").read()
    sparql.setQuery(selectSubjectsQuery)
    subjectResults = sparql.query().convert()
    subjects = list()
    for p in subjectResults["results"]["bindings"]:
        subjects.append(p["subject"]["value"].replace("\n",""))
    # Get a list of all genre strings in HTRC
    selectGenresQuery = open(app.config["ELEPHANT_QUERY_DIR"] + "select_genres.rq").read()
    sparql.setQuery(selectGenresQuery)
    genreResults = sparql.query().convert()
    genres = list()
    for p in genreResults["results"]["bindings"]:
        genres.append(p["genre"]["value"])
    return render_template("construct.html", persons = persons, places = places, subjects = subjects, genres = genres)







