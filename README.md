# DSTC6 Track2: End-to-End Conversation Modeling Track

1. Main task (mandatory): Customer service dialog using Twitter

    (*) The tools to download the twitter data and transform to the dialog format from the data are provided. 


    Task A: Full or part of the training data will be used to train conversation models. 

    Task B: Any open data, e.g. from web, are available as external knowledge to generate informative sentences. But they should not overlap with the training, validation and test data provided by organizers.

2. Pilot task: Movie scenario dialog using OpenSubtitle

# Necessary steps

## Twitter task

1. prepare data set using `collect_twitter_dialogs` scripts.

    ```
    $ cd collect_twitter_dialogs
    $ collect.sh
    ```
    (a twitter account and access keys are necessary to run the script. follow the instruction in `collect_twitter_dialogs/README.md`)
   
2. extract training, development and test sets from stored twitter dialog data
    
    ```
    $ cd ../tasks/twitter
    $ make_trial_data.sh
    ```
    
    Note: the extracted data are trial data at this moment.

3. run baseline system (optional)

    ```
    $ cd ../../ChatbotBaseline/egs/twitter
    $ run.sh
    ```
    
    (see `ChatbotBaseline/README.md`)

## OpenSubtitles task

1. download OpenSubtitles2016 data

    ```
    $ cd tasks/opensubs
    $ wget http://opus.lingfil.uu.se/download.php?f=OpenSubtitles2016/en.tar.gz
    $ tar zxvf en.tar.gz
    ```

2. extract training, development and test sets from stored subtitle data 

    ```
    $ make_trial_data.sh
    ```
    Note: the extracted data are trial data at this moment.

3. run baseline system (optional)

    ```
    $ cd ../../ChatbotBaseline/egs/opensubs
    $ run.sh
    ```
    
    (see `ChatbotBaseline/README.md`)

## Directories and files
* README.md : this file
* tasks : data preparation for each subtask
* collect_twitter_dialogs : scripts to collect twitter data
* ChatbotBaseline : a neural conversation model baseline system

