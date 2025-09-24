# `moji_namer` version 0.0.2

`moji_namer` is a python package for to make ChatGPT API calls to rename picture files.

## Example

Given a simple JPEG file of say 512x512 pixels describing a scene, we would like to give it a relevant name such as `ready_to_eat_fork_knife.jpg`.

![example.jpg](example.jpg)

## Use case

We have a directory of about 200 such images, and we would like to rename them all automatically.

## Call

Set the API Key:

    export OPENAI_API_KEY="<place key here>"

This is how you call the script:

    $ ./moji_namer ~/path/to/directory/with/pictures/

And it will batch rename all the pictures. No backup is made. The user must handle that.
