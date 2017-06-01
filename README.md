# DSTC6 End-to-end Conversation Model Task

# Necessary steps

## Twitter task

1. prepare data set using collect_twitter_dialogs scripts.

    (see collect_twitter_dialogs/README.md)
   
2. extract training and development sets from stored twitter dialog data

    use make_trial_data.sh in tasks/twitter.

    Note: the extracted data are trial data at this moment.

3. run baseline system (optional)

    copy the data files into ChatbotBaseline/egs/twitter and
    execute 'run.sh' in ChatbotBaseline/egs/twitter.
    (see ChatbotBaseline/egs/twitter/README.md)

## OpenSubtitles task

1. download OpenSubtitles2016 data:

    http://opus.lingfil.uu.se/download.php?f=OpenSubtitles2016/en.tar.gz

    and extract xml files by

    $ tar zxvf en.tar.gz

2. extract training and development sets from stored subtitle data 

    use make_trial_data.sh in tasks/opensubs.

    Note: the extracted data are trial data at this moment.

3. run baseline system (optional)

    copy the data files into ChatbotBaseline/egs/opensubs and
    execute 'run.sh' in ChatbotBaseline/egs/opensubs.

    (see ChatbotBaseline/egs/opensubs/README.md)

## Directories and files
- README.md : this file
- tasks : data preparation for each subtask
- collect_twitter_dialogs : scripts to collect twitter data
- ChatbotBaseline : a neural conversation model baseline system

