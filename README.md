# eval_project
Develop evaluation and report generation tool for P532 Object-Oriented Software Development 

I use python , sqlAlchemy, flask, mysql. sqlalchemy is python library for mysql database connection. flask is python framework for web development.

To run locally in ubuntu, you may need to install python 2.7, sqlalchemy 0.8.4, flask 0.10.1, mysql.

database_setup.py - it connects to a database(in my case, 'mysql://root:your_password@localhost:3306/eval'), and create database table, you may need to create a database (e.g. 'eval') first before runnint it

populate_database.py - populate the database by some dummy data

main.py - routes urls. 
    /main                       entry page. 
    /reports/semester_id/week   reports for semester_id, week where semester_id and week are int
    
templates/ - html templates
