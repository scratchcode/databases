title: What is a database?
slug: 00-what-is-a-database





# What is a database?

Database is usually short for Database Management System, though people also use database to refer to a specific set of data. From now on, when I say database I mean Database Management System, for example, something like postgresql.

So, what is it?

Let's start with what [the wiki](https://en.wikipedia.org/wiki/Database) says:

> [A database is an] application that interacts with the user, other applications, and the database itself to capture and analyze data. A general-purpose DBMS is designed to allow the definition, creation, querying, update, and administration of databases

From that we already know a few things it has to do: deal with user input and output, have ways for other applications to interact with it, and well, manage the data.



## Data storage

One of the jobs of the database is to ensure data persistence. Data should not be lost if the database stops running for whatever reason. A good database will preserve the data even in the case that itself crashes, or the computer it is running on is turned off without exiting the database gracefully. More concretely, the database ensures data is stored in files on a hard drive.

Since reading and writing from disk is [a lot slower](https://people.eecs.berkeley.edu/~rcs/research/interactive_latency.html) than reading and writing to memory and a lot more data fits on disk than in memory, the database will have to manage which parts of the data are kept in memory and what to do when a required part is not there.

Furthermore, a representation of the data that is convenient for some tasks is not convenient for other tasks. The prime example here is that on disk, the data should be compressed as much as possible to save time and space, but the user should be presented the data in human-readable format. So, the database will need to manage the various representations along with the metadata (data about the data) that it needs in order to achieve those representations.



## User interaction

The database should make available a set of human-friendly commands for the user to store and retrieve data in the database. This implies that the database needs to be able to parse user input and offer useful error messages when said input is formatted incorrectly. Things can get complciated quickly here deppending on how flexible the syntax of the database language is.

Besides storing and retrieving a single piece of data, it will be likely that the user needs to query the database to see what pieces of data match a given condition. This will add complexity to both the database language and to the data storage: we need to have syntax to describe the operations concisely and we also need to implement the operations efficiently.

An important, though not strictly necessary, feature of a database is to allow the user to describe the logical structure of the data ahead of time. This logical structure is called the schema of the data. The database should let the user specify what fields a records in the database have and also let the user have different types of records. For example, instead of simply letting the user store things like:

```
{client_name:Paco Sanchez, account_number:1}
{account_number:1, balance:1000}
{client_name:John Smith, account_number:2}
{account_number:2 balance:500}
{client_name:, account_number:3, country:Switzerland}
```

the database should let the user describe the fact that there are two tables, one for clients and another for accounts, and what fields each is expected to have. This could go further: the user should be able to specify whether a field is optional, and what type of data goes in it.

One way to accomplish this would be to have a language used to describe the data schema in addition to the language used to perform operations on the database. In practice, though, it is common for the same language to serve both purposes.



## Interaction with other applications

In addition to interacting with a human user, the database usually needs to interact with other pieces of software, for example a web server or a web application. In fact, we can think of user interaction as a special case of this: the database interacts with a piece of software whose job is to interpret user input, send it to the database, and show the output to the user. Such a program would be called a client, in which case our database becomes a database server.

One natural thing to want from a database server is that it supports multiple clients simultaneously. In fact, that's what happens in the databases that web applications use. This introduces a new kind of complexity: the database has to be able to cope with things happening simultaneously. What if client 1 says that the value of the `balance` in the record `account_number:1` should be `500` and another that it should be `1000` and both clients made their statements at the same time. Not only that, but what if the database is bogged down writting some big record that one client sent when another client wants to read a different record? All these are problems of concurrency and real-world databases deal with them.

So, interacting with other applications brings about two more things for our database to do: manage client connections and deal with concurrency.



## Transactions

Suppose we wanted to capture this event: a user moves $50 from one account to another. We have to update two records in our database: decrease the balance in one account by 50 and increase it in another by 50. To the user this is really one operation `move $50 from this account to that one` but to our database it is two operations, an update for the records of the accounts involved. What if the database crashes right after the first operation is complete? $50 goes missing! Similarly, if only the second operation succeeds, then $50 appear out of thin air.

A good database should offer a way of dealing with this — a way to say "the following operations are all or nothing". The fancy name for that abstraction is [ACID transactions](https://en.wikipedia.org/wiki/ACID) and a good database supports them.



## Replication, availability, and consistency

Since users often want the data to be safe and always available, databases provide several mechanisms for replication. The simplest version of this is a program that connects to the database and generates a single file with all the data, ie a backup. Besides those, databases often have automatic replication: copies of each piece of data stored in the database are made automatically to other instances of the database running elsewhere. This is often done with two aims. First, letting the user get their application back to operational quickly in case a the computer running the database crashes or becomes unavailable for some reason (e.g. a problem with the network). Replication adds availability (and complexity!).

As soon as we introduce the notion of having many instances of the database, we have to deal with the possibility that instances may be inconsistent with one another. The various strategies employed to deal with these are called consensus algorithms, and again, most modern database systems offer these features.



## Anything Else?!

Fortunately, no, that's about it. But as you can imagine, each of these features of the database can be very complex. While a competent programmer could write a database that does some version of each of the things above in a few weeks, in a real system (like postgres) tens to hundreds of programmer-years have gone into each component.



## Further Reading

To write this I either read or skimmed the following, they may be useful to you, too:

* [Chapter 1](http://infolab.stanford.edu/~ullman/fcdb/ch1.pdf) of *Database Systems: The Complete Book* by Garcia-Molina, Ullman, and Widom
* The intro chapter of the red database book
* Wiki links and others
* the design doc of cockroach

I didn't read these, but I bookmarked them in the process of writing this:

* the red book
* the postgres paper







