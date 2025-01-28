# Library-Database

## Project Overview
This **Library Database** is designed to manage information about authors, their works and the numerous editions of these works. Additionally, the database stores the average ratings of each work, as well as maintains author bibliographies from various sources. It also handles the specialization of editions as physical or digital or both formats.


## Data Sources
The two data sources used to populate our databases were from Open Library API and MediaWiki. Open Library provided  the main sources of information such as literary works, editions, ratings, and authors. It allowed us to create and populate the main structure of the database. MediaWiki was used to gather supplementary information for the authors, mainly additional biographical information. This allows the population of the bio entity to allow multiple bio’s, from different sources, to a single author.


## Implementation
The database and queries were developed using PostgreSQL and pgAdmin4.

# SQL DATABASE: Postgresql
The SQL database system was designed to manage information about works, their authors, bibliographies, editions, and ratings. Information for the database was populated by joining the Open Library API and Wiki API API’s. The core of the system consists of works and authors which expands to include tables of additional related information. Below are the main components of the system:
### 1. Authors
  - Entity: maintain information about the author such as author id and name. 
  - Relationships:
    - Strong entity in relation with the weak entity bio 
    - Many to many relationship with the works entity
### 2. Work
  - Entity: represents the individual created work with attributes such as title and publish date.
  - Relationships: 
    - Many to Many relationship with authors
    - One to One relationship with rating
    - One to many relationship with editions
### 3. Bio
  - Entity: Stores multiple bibliographical information about each authors
  - Relationships:
    - Weak entity of the weak entity relationship with authors
### 4. Ratings
  - Entity: Provides the average user feedback per work with attributes such as average rating and rating count.
  - Relationships:
    - One to One relationship with works
### 5. Edition
  - Entity: Specific edition of works, including attributes such as isbn10 and publish date.
  - Relationships:
    - Many to one relationship with work
  - Specialization: Edition is split into an ISA relationship containing
    - Physical Edition: storing edition form
    - Digital Edition: storing edition type


