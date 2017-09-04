# Scripts to acquire twitter dialogs via REST API 1.1.

Copyright (c) 2017 Takaaki Hori  (thori@merl.com)

This software is released under the MIT License.
http://opensource.org/licenses/mit-license.php

## Requirements:

* 64bit linux/macOSX/windows platform

* python 2.7.9+, 3.4+

    note: With python 2.7.8 or lower, InsecureRequestWarning may come out  
          when you run the script.  To suppress this warning, your can  
          downgrade the requests package by  

    ```
    $ pip install requests==2.5.3
    ```

     or

    ```
    $ pip install requests==2.5.3 -t <some-directory>
    ```

    where we assume that the module has been installed in &lt;some-directory&gt;

## Preparation

1. create a twitter account if you don't have it.

    you can get it via <https://twitter.com/signup>

2. create your application account via the Twitter 

    Developer's Site: <https://dev.twitter.com/>

    see <https://iag.me/socialmedia/how-to-create-a-twitter-app-in-8-easy-steps/>  

    for reference, and keep the following keys

   * Consumer Key
   * Consumer Secret
   * Access Token
   * Access Token Secret  

3. edit ./config.ini to set your access keys in the config file

   * ConsumerKey
   * ConsumerSecret
   * AccessToken
   * AccessTokenSecret  
  
4. install python modules: six and requests-oauthlib

    you can install them in the system area by

    ```
    $ pip install six
    $ pip install requests-oauthlib
    ```

    We recommend to use virtualenv or some other virtual enviroment to handle pythone modules.
Otherwise, you can specify the directory to install python modules as

    ```
    $ pip install <module_name> -t <some_directory>
    ```
    In this case, &lt;some-directory&gt; must be included in `PYTHONPATH` environment
    variable to use the modules.

## How to use:

1. Execute the following command to test your setup

    ```
    $ collect_twitter_dialogs.py AmazonHelp
    ```

    and you will obtain a file `AmazonHelp.json`, which contains
    dialogs from AmazonHelp twitter site.

    since the `AmazonHelp.json` is raw data, you can see the dialog text by 

    ```
    $ view_dialogs.py AmazonHelp.json
    ```

2. Use `collect.sh` to acquire large data using an account list

    ```
    $ collect.sh
    ```

    You will find the collected data in `./stored_data`

    ```
    $ ls stored_data
    AmazonHelp.json   AskTSA.json ...
    ```

    To acquire a large amount of data, it is better to run this script
    once a day, because the amount of data we can download is limited
    and older tweets cannot be accessed as time goes by.

    In the first run, it will take a several hours to collect all possible
    data from the listed accounts, but from the second time, the time will
    become much shorter because the script downloads only newer tweets than 
    already collected tweets.

    Note: the script sometimes reports API errors, but you don't have
    to worry. Most errors come from access rate limit by the server.
    Even if the script accidentally stopped, there is no problem.
    Just re-run the script.

3. Use `official_collect.sh` to acquire official data for DSTC6 End-to-End Conversation Modeling track

    ```
    $ official_collect.sh
    ```

    Each challenge participant must run the script by at least 9/8/2017 GMT 24AM (Midnight)
    and do it once a day until 9/18/2017.
    This can be done easily by the following command:

    ```
    $ watch -n 86400 official_collect.sh
    ```

    (The `watch` command will run `official_collect.sh` every 24 hours)

    You will find the collected data in `./official_stored_data`

    ```
    $ ls official_stored_data
    1800flowershelp.json   1800flowers.json   1800PetMeds.json   1DFAQ.json
    1Sale.json ...
    ```

    A script to extract training, development, and test sets will be provided around 9/18/2017.
