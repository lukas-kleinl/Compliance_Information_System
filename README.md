# Compliance_Information_System
Provide information about GDPR and company controls and also enable creating, editing and deleting them

## Table of Contents

1. [Introduction](#introduction)
2. [Features](#features)
3. [Installation](#installation)
4. [Usage](#usage)
5. [Configuration](#configuration)
6. [Contributing](#contributing)
7. [License](#license)
8. [Contact](#contact)
9. [Acknowledgements](#acknowledgements)

## Introduction

Finding relevant information about the compliance within a company is very important. 
Furthermore the complex legal landsacpe around makes it hard for employees to find relevant information. 
Therefore the goal of this work is a first prototype to solve this problem

## Features

- Maintenance of company controls - Policies, Guidelines
- GDPR exploration with a graph based approach
- Providing relevant information in a human readable fashion with a large language model

## Installation

The app is build based on 4 Flask packages. 
In each package the requirements are provided. 
Install these either locally or in a virtual environment.
Furthermore follwing services need to be installed or setup:

- MongoDB with Atlas Vector Search
- Neo4j instance
- Ollama or another LLM (needs to be configured)
- Okta for authorization

For the configuration details an .env needs to be set up with following relevant information: 

###Recommender Package

AURA_DB_URI = "bolt://localhost:xxxx"  - normally 7687  
AURA_DB_USERNAME = "neo4j"  
AURA_DB_PWD = "anypassword"

### Policy Manager package
MongoDB_URI = mongodb+srv://lukaskleinl:xxx@cluster.xxxx.mongodb.net/?retryWrites=true&w=majority&appName=Cluster - Looks something like this if setup in cloud  
If setup locally the correct URI needs to be provided

### Compliance Authorization package - information can be found in OKTA
URL for Okta: https://manage.auth0.com/dashboard/eu/dev-lpidbb8cgvdmuria/  
AUTH0_CLIENT_ID=xxxx  
AUTH0_CLIENT_SECRET=xxx  
AUTH0_DOMAIN=dev-lpidbb8cgvdmuria.eu.auth0.com  
APP_SECRET_KEY=ALongRandomlyGeneratedString  
  
URL_Recommender = http://127.0.0.1:2001/  
URL_Company_Control_Store = http://127.0.0.1:2002/  
URL_Chat = http://127.0.0.1:2003/


### Compliance LLM Recommender package
Here a Open API Key was used for the embedding for the vector search.   
Another embedding like Ollama can also be used. An Open API Key is not needed in this case. 
The key can be found in the webpage after login to OpenAI  

OPENAI_API_KEY = xxxx  
MongoDB_URI = mongodb+srv://lukaskleinl:xxx@cluster.xxxx.mongodb.net/?retryWrites=true&w=majority&appName=Cluster  


Afterwards run follwing commands with the given ports:
  
Authorization and routing - flask run --host=0.0.0.0 --port=2000    
GDPR exploration - flask run --host=0.0.0.0 --port=2001  
Company Controls Manager - flask run --host=0.0.0.0 --port=2002  
LLM recommender - flask run --host=0.0.0.0 --port=2003

### Prerequisites

- MongoDB with Atlas Vector Search
- Neo4j instance
- Ollama or another LLM (needs to be configured)
- Okta for authorization

### Steps

1. Clone the repository:

2. Navigate to the project directory:

3. Install requirements

4. Create .env files

5. Run flask apps with given ports

## Usage

Start up all servies and open your localhost at 2000. 
The authorization and routing package running on port 2000 is the starting point for all operations
If everything is running the opened site should be self explanatory and the functionality can be tested.
