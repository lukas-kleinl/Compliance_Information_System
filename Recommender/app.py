import requests
from flask import Flask, render_template, jsonify, request, Response, abort
from neo4j import GraphDatabase
import neo4j.time
from dotenv import load_dotenv
import os

from rdflib_neo4j import Neo4jStoreConfig, HANDLE_VOCAB_URI_STRATEGY, Neo4jStore
from rdflib import Graph

app = Flask(__name__)

#Load Configuration from .env file
load_dotenv()
AURA_DB_URI = os.getenv("AURA_DB_URI")
AURA_DB_USERNAME = os.getenv("AURA_DB_USERNAME")
AURA_DB_PWD = os.getenv("AURA_DB_PWD")
driver = GraphDatabase.driver(AURA_DB_URI, auth=(AURA_DB_USERNAME, AURA_DB_PWD))

auth_data = {'uri': AURA_DB_URI,
             'database': "neo4j",
             'user': AURA_DB_USERNAME,
             'pwd': AURA_DB_PWD}

config = Neo4jStoreConfig(auth_data=auth_data,
                          handle_vocab_uri_strategy=HANDLE_VOCAB_URI_STRATEGY.IGNORE,
                          batching=True)

neo4j_aura = Graph(store=Neo4jStore(config=config))

#dataset to download from the web // rdf file format
#dataset = "https://old.datahub.io/dataset/92481a73-d12e-4565-98a0-41d737d3e09a/resource/34b9eac2-96db-4afa-ba3f-a33f21f1b2b2/download/gdpr.rdf"

#Locally downloaded from https://github.com/coolharsh55/GDPRtEXT/blob/master/gdpr.rdf
dataset = "./static/gdpr.rdf"

neo4j_aura = neo4j_aura.parse(dataset, format="xml")
neo4j_aura.close(True)


@app.before_request
def limit_remote_addr():
    if request.remote_addr != '127.0.0.1':
        abort(403)


def serialize_neo4j_value(value):
    """"**Serialize neo4j value"""
    if isinstance(value, (neo4j.time.Date, neo4j.time.DateTime)):
        return str(value)
    return value


def serialize_node(node):
    """Node serialization"""
    return {
        'id': node.id,
        'labels': list(node.labels),
        'properties': {k: serialize_neo4j_value(v) for k, v in node.items()}
    }


def serialize_relationship(rel):
    """Serialize the relationships"""

    test = {k: serialize_neo4j_value(v) for k, v in rel.items()}
    for key in test:
        print(key)

    return {
        'id': rel.id,
        'startNode': rel.start_node.id,
        'endNode': rel.end_node.id,
        'type': rel.type,
        'properties': {k: serialize_neo4j_value(v) for k, v in rel.items()}
    }


@app.route('/')
def index():
    """basic buildup of the GDPR home"""
    valid_filters = [
        "Article", "Chapter", "Citation", "LR", "LRS", "LegalResourceSubdivision", "Point", "Policy", "Recital",
        "Resource", "Section", "SubPoint"
    ]
    return render_template('index.html', valid_filters=valid_filters)


@app.route('/graph')
def get_graph():
    """Buidling the graph"""
    filter_value = request.args.get('filter')
    node_id = request.args.get('id')
    if filter_value:
        query = f"""
        MATCH (n:{filter_value})-[r]->(m)
        RETURN n, r, m
        """
    elif node_id:
        query = f"""
        MATCH (n)-[r]->(m)
        WHERE id(n) = {node_id}
        RETURN n, r, m
        """
    else:
        return jsonify({'error': 'No filter or ID provided'})

    nodes = []
    relationships = []
    try:
        with driver.session() as session:
            result = session.run(query)
            for record in result:
                n = record['n']
                r = record['r']
                m = record['m']

                nodes.append(serialize_node(n))
                nodes.append(serialize_node(m))
                relationships.append(serialize_relationship(r))
    except Exception as e:
        return e, 404

    return jsonify({
        'nodes': list(nodes),
        'relationships': relationships
    })


@app.route('/node_relationships')
def get_node_relationships():
    """"""
    node_id = int(request.args.get('node_id'))
    incoming_rels = []
    outgoing_rels = []
    try:
        with driver.session() as session:
            query_incoming = """
            MATCH (n)<-[r]-(m)
            WHERE id(n) = $node_id
            RETURN r, m
            """
            result_incoming = session.run(query_incoming, node_id=node_id)
            for record in result_incoming:
                rel = record['r']
                start_node = record['m']
                information_incoming = {
                    'id': rel.id,
                    'type': rel.type,
                    'startNode': start_node.id,
                    'properties': {k: serialize_neo4j_value(v) for k, v in start_node.items()}
                }
                incoming_rels.append(information_incoming)

            query_outgoing = """
            MATCH (n)-[r]->(m)
            WHERE id(n) = $node_id
            RETURN r, m
            """
            result_outgoing = session.run(query_outgoing, node_id=node_id)
            for record in result_outgoing:
                rel = record['r']
                end_node = record['m']
                information_outgoing = {
                    'id': rel.id,
                    'type': rel.type,
                    'endNode': end_node.id,
                    'properties': {k: serialize_neo4j_value(v) for k, v in end_node.items()}
                }
                outgoing_rels.append(information_outgoing)
    except Exception as e:
        return e, 404

    return jsonify({
        'incoming': incoming_rels,
        'outgoing': outgoing_rels
    })


if __name__ == '__main__':
    app.run()
