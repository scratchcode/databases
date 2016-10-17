title: Designing a simple key-value store
slug: 01-design-key-value-store

Alright, let's get coding!

Psych. We have to figure out what to code first.

What's the simplest thing we can make that could pass for a database?

Let it be a single-user (i.e. no concurrency), append-only (we never actually delete data from files), key-value database (the simplest logical structure for the data) without transaction support.

Our database will only have 3 operations available to the user: set a key to a value, get the value associated with a key, and delete a key and its associated value. This will make the query language and the internal workings of the database simple.

Note that offering a delete operation to the user is not the same as actually deleting the underlying data. Instead, our database can keep track of what data has been deleted. This may seem like a complication, but it makes it easier to reason about the data and the operations on it.

As a further simplification we'll make our database use two files — one for keys, and the other for values.  We could employ one of various strategies to make all the data live in one file, but this will be easier.

If all these simplifications seem like they add up to a database that isn't very useful it is because they do! We'll add missing bells and whistles later.

We'll work in python and with the rule that we can use anything in the standard library and nothing outside of it. We'll also follow the guideline that we are trying to do as much as possible by hand.

We need this guideline because python's standard library is so rich that there are not [one](https://docs.python.org/3.5/library/shelve.html), but [two](https://docs.python.org/3.5/library/dbm.html) databases of this sort in there.[1] The standard library also has all kinds of other tools to make life easier. Who would want an easy life? We're trying to code from scratch.



[1]: Bear in mind that both of those are databases with python interfaces, but without query processors and clients. You use them by writing python code to call the functions in their API. We're trying to do a little bit more than that here, but if your day job was to make a key-value store in python with a query language and a client, it'd be best to focus on the language and client and let the built-in databases do the rest.


# 10k foot view

We know we'll need the following:

- data spec: what is allowed in the database and how to represent it
- physical layer: in charge of operations on files
- storage format: specify what we'll write in the file
- logical layer: maintain a representation of the data in memory
- database API: python methods that expose the database functionaltiy
- query language: specify the syntax for the commands available to the user
- query processor: validate user input, execute the associated functions when it is, and generate output
- client: interacts with the user, sends input to the database and shows the output to the user

Don't worry if why we need all these things isn't clear. It'll become clearer as we go. The main reason there are so many components is that it is easiest to reason about a given component or spec when it is only [in charge of doing one thing](https://en.wikipedia.org/wiki/Single_responsibility_principle).

Before you move on, spend a few of minutes writing down how you'd implement or specify each of the things above. Ideally, you'd have a file with notes to guide your implementation. You can think of the rest of this section as a detailed version of such notes for the code that I designed and wrote.

The rest of this section specifies the above components in detail. Trying to produce the code yourself without further guidance at this stage is a very good, but possibily time consuming exercise. Try it! You can always come back to reading.

### How the code will be organized

The code in the tutorial is written "back-to-front" (arbitrary choice) i.e. starting with the component that is farthest away from the user and ending with the component that interacts with the user. More specifically, it roughly goes in this order: storage layer -> logical layer -> database API -> query processor -> client.

The [repository](https://github.com/scratchcode/scratchdb/) is organized so that each tag corresponds to a tutorial section.

Here's the [initial commit](https://github.com/scratchcode/scratchdb/commit/1847b895eb341afe88065c0029f8de28fe2ada4b).

And these are the tags:

[The physical layer, first pass](https://github.com/scratchcode/scratchdb/tree/physical-layer-first-pass)

---

# The minimal spec

## Data

Any python object that can be pickled will be a valid key or value i.e. `pickle` will serve both to specify what's valid and to serialize and de-serialize data.



## Storage format

We'll store data as raw bytes in a file that also stores the length of a piece of data along with it i.e. our file will look like `<size of the data, integer><data><size><data><size><data>... `.



## Physical layer

We'll write a wrapper around a python file object that exposes an API with methods to read and write in our format. The caller of this API won't have to deal with the length of the data, they can just read a given address. The physical layer will expose a `read()` method and only an `append()` method to write. The storage layer does not expose a method for deletion.



## Logical Layer

The logical layer will maintain 2 instances of the object from the physical layer, one for keys and one for values. It is responsible of orchestrating between these objects to implement the database operations. Keys will be represented as python tuples: `(key, value_address)`. The first element is the python object representing the key and the second is the address in the values file where the value is stored. To keep track of deleted data, we'll assume the convention that a key whose `value_address` is `None` is understood to be deleted. Notice that since our database is append-only, whenever we are asked to get the value of a key we can't return as soon as we find the key, we have to find the last copy of that key in the file — it's latest value.



## Database API

This will be the simplest component to write, it consists of a python class with 4 exposed methods: one for each of the database operations (`get()`, `set()` and `pop()`) and one to close the connection to the database: `close()` (which in our case is simply closing the underlying files). This object uses an instance of the logical layer. This object is really just an interface, it should contain very little functionality.



## Query language

Our language syntax will consist of  `<get or pop> <key>` and `<set> <key> <value>`. Whitespace is disallowed in keys. All our tokens can be separated by white space (so that we can use the built-in `split()` to tokenize). Any valid python expression can be used as a key or value. We're making these questionable choices to make implementing the query processor easy.



## Query processor

The query processor will have one method: `execute(query)` which either returns a string representing the result or the error message to display to the user. This object is responsible for enforcing the rules of the query language. We'll use the built-in `split()` to tokenize and `ast.literal_eval()` to parse keys and values. Whenever `ast.literal_eval()` fails, the given input will be interpreted as a string. We'll accept the "feature" that `set 2+2 "foo"` is the same as `set 4 foo`.  Since we're having the query processor handle validation and execution in a single function call, it'll be simplest if it has access to the relevant instance of the database API object.


## Client

We will write a command-line client, which will require specifying a database name along with the command in the shell i.e. the user would run it like so: `$ python toydb.py <path to database directory>`. The database directory is any directory that contains the keys and values files. The client will be a read-eval-print loop (usually called a [REPL](https://en.wikipedia.org/wiki/Read%E2%80%93eval%E2%80%93print_loop)) which will use an instance of the database API object and one of the query processor. The client will interpret `Ctrl-d` and `Ctrl-c` as exit commands.


---


If theis spec seems sufficient to start coding, you can skip to [LETS START CODING]. The rest of this section goes into more detail about how to arrive at the spec above. It is a good, but time consuming, exercise to start coding using the spec above and only refer to the detailed explanations when you get stuck.

---

# The minimal spec explained

## Data

What kinds of data should the user be able to store as values? What are valid keys? You may think that the best possible answer here is "anything!" and that's close, but there are exceptions.

Should the user be able to store an object that represents a connection to a server? In a sense, yes, the object is just a bunch of bytes and we could write those bytes to disk and let the user retrieve those bytes later. But, in the majority of cases, when such an object is retrieved it'll be useless. To understand why we'd have to go into a bit of a rabbit hole, but take my word for it.

One way to go about answering the question is to defer it to the user: the database can store any set of bytes you give it. Let the user worry about how to turn their stuff into bytes and what to do with them when the database returns them. In fact, this is the approach that [dbm](https://en.wikipedia.org/wiki/Dbm) takes, which is one of the databases that is built-in to the python standard library.

The process of turning stuff into bytes is called serialization. Letting the user deal with that is a fine solution, but it limits the ability of the database to pack data densely in the file and to use time-efficient data structures to represent it. What if the user decides that the integer `1` should be represented by 100 bytes set to the value `0xff` (100 bytes that look like`11111111`) and then proceeds to just store the value `1` on a bunch of keys. This would interfere with two of the tasks of the database which is to store data efficiently and manipulate it efficiently. It'd be way more efficient to store the `1` as the byte `0x01` (ie `00000001`) once and just have the keys point to the same value. That way both storage and database operations would be very efficient.

This is a general tradeoff: the more you know about the data, the more efficiently you can manipulate it and store it, but you have to do more work to specify what's allowed and the more you have to constrain the user.

So, the more common approach is for the database to specify a set of types of objects that it supports. In the case of a key-value store, like we're building, this applies to both keys and values. This is what [shelve](https://docs.python.org/3.5/library/dbm.html), the other built-in database mentioned above, does. The keys have to be python strings and the values can be any python object that the [pickle](https://docs.python.org/3.5/library/pickle.html#what-can-be-pickled-and-unpickled) module knows how to serialize. This is a pretty sensible approach, so let's do something very similar.

In our case, we'll allow anything that can be pickled (haha, get it?) for both keys and values.



## Storage format

Now that we know what we'll be storing, let's worry about how.

We'll be writing our data to a file on disk and since our database has to support havign many keys and many values, we have to do some form of organizing in order to be able to store them in a sane way. After an object (ie a key or value) has been serialized it looks like a bunch of bytes ie a bunch of 0s and 1s. If we just store them one after the other in the file, we don't know which bytes go with which object. For example, we store the bytes for the key `key1` and then the bytes for `key2`. The bytes for `key1` look like (using python's syntax for raw-byte strings) `b'\x80\x03X\x04\x00\x00\x00key1q\x00.'` and the ones for `key2` look like `b'\x80\x03X\x04\x00\x00\x00key2q\x00.'` So, in our file we'd have `b'\x80\x03X\x04\x00\x00\x00key1q\x00.\x80\x03X\x04\x00\x00\x00key2q\x00.`. If we read all those bytes and have pickle deserialize them, we don't get `[key1, key2]` or anything resembling both of our keys. Try it in your python shell.

```python
import pickle
bs1 = pickle.dumps('key1')
bs2 = pickle.dumps('key2')
bs = bs1 + bs2
pickle.loads(bs1 + bs2)
```

What did you get?

I know it wasn't our keys.

So, at minimum, we need a way to remember where in the file a value's (or key's) bytes end. And not only that, but we need to store this along with the data so that we can read it later. The easiest way to deal with this is to store the size right before the data. So, for example, if we had these bytes `b'\xff\xff'` (2 bytes filled with 1s), we could write their size (2) along with the data. So, we'd store something along the lines of `b'\x02\xff\xff'` i.e. use one byte to represent the size of the data and then the bytes that represent the data. So, our data on disk would look like `<size><data><size><data>...`

This is pretty good, but it has one problem: since a byte is 8 bits ie 8 zeroes or ones, it can store at most 2^8 - 1 = 255. That means that our database could only store values of data that are smaller than 255 bytes. Not too great.

There is another problem: how do we represent numbers? Is the number 2 represented as `01000000` or as `00000010` ie as `b'\x80' or as b'\x02`.

To solve both of these we need to agree on an integer format. And we need to make sure that we can represent integers big-enough to be useful. The good news is that the range of values we can represent grows exponentially with the nubmer of bytes we allocate to represent the integers. We are at liberty to pick whatever integer representation we want, so let's make them long long, unsigned, big-endian integers. Long long means we'll use 8 bytes to represent each, unsigned means we won't bother representing negative numbers, and big-endian means that the least-significant bit is at the end, not at the beginning. In our implementation we'll use the standard library's `struct` module to handle the actual conversion between python ints and bytes.

One last thing about this: if our data is 20 bytes long and we use 8 bytes to store its size should we think of it as data of size 20 or of size 28? This is arbitrary, one way or the other we'll have to do some bookkeeping, but we have to pick one. So we'll choose to include the size of the bytes storing the size in the size. i.e. we'll write 28 in the file for a piece of data that is 20 bytes in size. Size! Say size again!



## Physical layer

The physical layer of our database will consist of a class that is a wrapper around python's built-in `file`. It'll have internal methods to perform it's necessary operations and it will expose methods to read and _append_ to the file and to close it. Remember that we decided to make it so that we don't delete data from our database, so there is no delete operation.

Our physical layer will be in charge of dealing with the size of data. The layer that uses the physical layer aka "the caller" is the logical layer. In the logical layer we want to write code along the lines of `storage.append(data)`. Our physical layer will make that possible by taking care of measuring the size of the data and writing its size to the file before it. Ditto when reading data.

Having the physical layer be responsible for dealing with the size of data may seem a bit arbitrary at first. Why should it be the physical layer that deals with the size and not the logical one? Why shouldn't we expose a method that is used like `storage.append(data_bytes, size_bytes)` and have the caller deal with it?

We could do it that way, but it'd be bad design. The physical layer's single responsibility is to deal with the details of our data storage format. If the storage format changes in any way (for example, we decide to use fewer bytes to store the size), the logical layer should remain unchanged.

The physical layer has to to deal with the sizes of the data and with what byte goes where and where it's current pointer into the file is pointing (that's the abstraction that `file` objects offer). It does not deal with things like determining whether something is a key or a value or noticing that this key already exists and so some data should be updated or anything of the sort. That's where the responsibilities of the logical layer begin.



## Logical layer

The logical layer is, in a sense, where the core of the database is implemented. The user thinks of the operations the database offers (set, get, pop) and the data they are manipulating. The logical layer is concerend of making all that happen. The logical layer is called that because this is where the logical representation of the data lives — we are writing a key-value store, so our logical layer will contain an implementation of a key-value data structure.

The logical layer is also tasked with orchestrating with the storage layer. That is, it maintains instances of the storage object and uses them to persist data to disk.

If you started complaining that this violates the single responsibltiy principle, kudos to you! It a sense it does: is the logical layer in charge of the logical operations allowed on the data? or is it in charge of orchestrating? One way or another, something will have to orchestrate, and if we get too principled about single-responsibility we'll start having lots of classes that do very little and while that will be good locally (each of those classes will be easy to write) it'll be difficult to think of our system globally. This tradeoff is very general: the smaller your abstractions the more indirection between them you'll have. One way or another, you'll have to draw the line somewhere.

In this case, we're drawing the line here: the logical layer will expose operations to set, get, and pop keys, and to close the storage objects. The logical layer will also be in charge of serializing the keys and values into bytes.

To accomplish all this the logical layer will use two instances of our physical layer i.e. two files: one for keys and the other for values.

So, we need to specify what kinds of objects we'll use to keep track of keys and values. Since the physical layer abstracts storage for us, we only need to think about python objects and how to turn them into bytes. We made choices earlier to make this easy: we decided we'll store anything that `pickle` can serialize, and conveniently, that means we can use pickle to serialize it!

We'll represent keys as python tuples `(<key>, <address of value>)` and values just as themselves. The reason we don't simply store keys the same way as we store values is that we have to fetch the associated value somehow when we're given the key (i.e. we need to implement the `get` operation). Don't worry if this doesn't make perfect sense right now, it'll become clearer as we code.

Remember that our database does not delete data. I made that choice to simplify the implementation of the logical layer. To really reap the benefits, let me take it a step further here: not only does the database not delete data, it won't modify any data. To update the value that goes with a key, we simply store another copy. Finally, to implement `pop` we'll just store a key with `None` for the address of its value. This simplifies the implementation in two ways: one, `pop` and `set` become the same operation and two, we won't have to deal with the size of data changing when we modify it (this is technically a concern for the physical layer).

There are two downsides to having the database be append-only, though. One is that `get` becomes slightly more complicated: we have to look through all of the keys before we can retrieve one. We need to know its latest value. This isn't too big a deal, though, since that isn't too different than going through the keys to find the value in the first place.

The second downside is that we'll have stale data stored in the files i.e. we'll have old versions of keys, and values that are no longer used stored in the files. Back when hard drives were small in capacity and expensive in dollars, this used to be a big deal and that's why most mature database systems aren't append-only. Nowadays, storage is much cheaper than it used to, and conceptual simplicity has become more valuable.

This is a general tradeoff of using append-only data structures: they are conceptually simpler but they take up more space and are less efficient to access. (The conceptual simplicity may not be too obvious at this stage, but it will become so when we start using more sophisticated data structures in our logical layer)

We're done specifying our logical layer, but let's go through an example to see the implications of making the database append-only. Suppose we executed the following commands:

```
set key1 foo
set key2 bar
set key1 chicken
get key1
pop key1
get key1
```

After the 1st command, we'd just have a single key object in the keys file and a single value in the values file, and after the 2nd command we'd have two of each as is intuitive. When we execute the 3rd command, we simply add another key to the keys file which would now contain 3 key objects `[(key1, address of foo), (key2,  address of bar), (key1, address of chicken)]` and the values file would have 3 values as well `[foo, bar, chicken]`. To retrieve key1 we'd iterate through the keys and we'd find key1 first up, but that key object would point us to `foo` which is not it's latest value. We have to iterate to the end to find the latest value,`chicken`. When we pop key1 we'd add another key object to the keys file `(key1, None)` which would not contain 4 key objects (3 of which are for key1!). When we do the last get, we'd find key1 3 times before finding it's latest version which has our representation of deleted. So we'd raise an error indicating that key1 isn't in the database.



[1]: If it wasn't that the pickle module has such a simple interface and is capable of serializing just about anything, we would be wise to have serialization happen in a layer or component of its own. In fact, it may still be desirable to do so in order to be able to use a different (perhaps more space-efficient) serialization formats and tools.



## Datbase API

You think the storage format and the logical layer were difficult to think about? Wait til you read this part!

Just kidding.

The database API is probably the simplest component we'll write. Since the actual operations of the database are implemented in the logical layer, this layer only exists to give a nice python interface to the user. In principle, having this in place allows us to easily replace or modify the storage layer without impacting users of the database.

The dabase API is a simple python class with a method for each of the database operations `set()`, `get()`, and `pop()` and one to close the connection to the database. Internally, it uses an instance of the storage layer.

If we implement this far we would've replicated what `shelve` or `dbm` do. We'd have a python module which has a class the user can instantiate to get a database, which supports some pre-defined operations, and so on.



## Query language

We want to provide more to the user than just a python interface. We'd like to build a complete program that expects input in its own specialized syntax. This is where the query langauge comes in.[1]

We have to support 3 operations. In all cases, the operations will involve specifying a `key`. And in 2 cases (get and delete) that'll be all that's needed. So, the simplest syntax for 2 of our operations take the form `<command> <key>`.  The remaining case (set) requires a value in addition, so it should be something along the lines of `<command> <key> <value>`.

The `<` and `>` just indicate that something is a place holder. We still have to define what strings are valid for each place holder.

Let's start with our commands, let's have them be `set`, `get` and `pop`. So, we know that for an input string to be valid, it must start with one of those 3 three-letter words.

We also know that keys and values can be python objects. So, any valid [python expression](http://stackoverflow.com/questions/4782590/what-is-an-expression-in-python) can go in the place of `<key>` and `<value>`. So, for example, all these would be valid user input:

```
set (1, 10) {'name': 'john', 'age': 40}
set "foo" 3
set "fool" 4
get "foo"
get foo
set foo 30
get {1:10, 2:20, 3:30}
pop "fool"
pop "dne"
set (1, 10) {'name': 'john', 'age': 40, 'bio': 'hi\ni am john!'}
```

And these would be invalid:

```
foo bar baz
setfoobar
set [1, 2} {3, 4, 5}
get
pop
get foo bar
```

One undesirable feature of allowing any python expression for the keys and values is that things like `set 2+2 4+4`  are valid input, but it is unclear whether the user means `set 4 8` or `set "2+2" "4+4"`. Not only that, but the easiest way to handle the input is to have the the standard library's expression parser deal with it, and in that case `2+2` will be the same as `4`. We'll have to go our of our way to make things like `2+2` represent strings (e.g. `"2+2"`) or to make them invalid. Let's decide to live with this for now, but we'll fix it later.

Should `set            foo          bar` be valid? It's ugly, but the meaning is clear, so yes. What about if the user had typed tabs instead of spaces? Still yes. This suggests that our language wasn't as well defined as we thought. It should be: `<command><white space><key>` and `<command><white space><key><white space><value>`. To make things a bit more readable, let's agree from now on that there is always whitespace between place holders. So, when we write `<thing> <other thing>` we really mean `<thing><white space><other thing>`. What counts as whitespace? Anything the standard library thinks is whitespace, which is readily accessible via the [split](https://docs.python.org/3.5/library/stdtypes.html#str.split) method built into python strings.

Another complication! What a about the following user input?

```
set foo
bar
```

Is that two invalid commands or the same as `set foo bar`?

The easiest is to think of that as 2 commands, so we'll just specify that a new-line character terminates a user input string. Different choices would be valid, but all the choices we made are the same ones that `split()` makes, so they'll make our life easier.

So many corner cases! And we're not done, yet.

As far as language design goes, this language looks as good as it can. However, we will encounter one complication. Consider the following command, which is valid:

`set (1, 10) {'name': 'jack jones', age: 37}`

When we try to parse it with our query processor (below), we'd like to break it down into its components, namely `<command> <key> <value>` and we expect that they are separated by whitespace. When we `split()` that string we'd get `['set', '(1,', '10)', "{'name':", "'jack", "jones',", 'age:', '37}']` and we'd have to do work to try to reasemble the pieces (tokens) that go together into the key and the ones that go into the value.

The root of the issue is that python expressions can contain whitespace.

So, we could deal with this by deciding that `<key>` and `<value>` can not contain white space, since white space is mostly optional in python expressions. e.g. `(1,10)` is the same tuple as `( 1, 10 )`. That'd almost work, except that then the above command would have no valid analogue because `jack jones` contains a space!

In principle, we could work really hard to solve this problem. We'd have to add tokens to what we interpret to be the `<key>` part of the command until we get a valid python expression and treat the rest as the value. Or something similar to that. This would be ugly and complicated, trust me. We could also solve it by using a proper parser (like the one the python interpreter uses to parse input, for example), but that seems like overkill.

Let's pick a simpler solution: we will not allow whitespace in keys.

That would make the above command invalid, but this one would be equivalent: `set (1,10) {'name': 'jack jones', age: 37}` and valid.

It is a bit of a bummer to disallow things like `my key` or `"my key"` from being valid keys, but this makes our life the simplest. Other possible solutions would be to allow only strings, delimited by quotes or single-quotes to be keys e.g. things like `"my key"` and `'my key'` would be valid, but `foo` would be invalid, it'd have to be `"foo"`. Allowing strings only would keep us from having numerical keys or keys with more than one piece of data (like `(1, 10)`). In a real system, we'd make an exhaustive list of things we want to allow and then produce a real parser for our language (what I said was overkill above).

Designing languages is generally goes like this — lots exceptions and corner cases. It is difficult to produce a language that is useful and easy to validate. The good news is that we'll defer most of the complications to the standard library since we're interested in coding a database from scratch, not in writing a language parser from scratch! But this is a glimpse into how complicated real-world systems are.

Lest we lose track, our language is:

`get <key>`, `pop <key>` and `<set> <key> <value>`, keys and values will be interpreted as python objects whenever possible and as strings otherwise, and keys cannot contain whitespace.



[1]: Calling a language with `set key`, `pop key` and `set key=value` a query language is a bit of a stretch. Afterall, there isn't real querying going on — you have to know what you are looking for to find it. However, as an abstraction, a query language is what we are specifying here. We'll make it more powerful later.



## Query processor

Now that we have the language specified, it is clear what the query processor does: it validates queries and then executes them. We'll put our query processor in charge of a slightly more general task, which again, violates the single responsibility principle a bit: the query processor takes a string with user input and returns a string with the output to show to the user. That output string can be a string representation of the database response to the user's command or an error message.

To do its work our query processor will rely on two tools in the standard library: `split()` and `ast.literal_eval()`. After validating that the input string is valid, the query procesor will simply call the right function in the database API and convert what it gets back into a user-friendly string.



## Client

The last piece! Exciting!

Our client will be so simple that a single python function with a few lines of code will suffice to implement most of it.

To start our client, in the command line, the user specifies the name of the database they will be working with. e.g. `$ python toydb.py testdb` The client is then in charge of opening a connection to the database `testdb` which under the hood we know is just opening two files. Since the user is really referring to a couple of files on disk, let us decide that the command-line argument is a path to a directory which contains the database files.

Our client will print a prompt for the user and wait for input. Whenever the user enters a line of input, it'll send that to the query processor for it to execute the input on the database or to reject it as invalid. The client then prints out whatever the query processor returned and prints the prompt again.

Pressing `Ctrl-d` or `Ctrl-c` tells our client to close its connection to the database and exit.

And, you guessed it! The sandard library makes all this easy.

---

# Further Reading

http://stackoverflow.com/questions/4782590/what-is-an-expression-in-python

https://docs.python.org/3/reference/expressions.html

https://docs.python.org/3.5/library/pickle.html#what-can-be-pickled-and-unpickled

https://docs.python.org/3.5/library/dbm.html

https://docs.python.org/3.5/library/shelve.html

https://en.wikipedia.org/wiki/Persistent_data_structure

https://en.wikipedia.org/wiki/Read%E2%80%93eval%E2%80%93print_loop

https://docs.python.org/2/library/struct.html#byte-order-size-and-alignment













