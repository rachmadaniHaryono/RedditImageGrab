[![Build Status](https://travis-ci.org/rachmadaniHaryono/RedditImageGrab.svg?branch=master)](https://travis-ci.org/rachmadaniHaryono/RedditImageGrab)
[![codecov](https://codecov.io/gh/rachmadaniHaryono/RedditImageGrab/branch/master/graph/badge.svg)](https://codecov.io/gh/rachmadaniHaryono/RedditImageGrab)

# RedditImageGrab

I created this script to download the latest (and greatest) wallpapers
off of image subreddits like wallpaper to keep my desktop wallpaper
fresh and interesting. The main idea is that the script would download
any JPEG or PNG formatted image that it found listed in the specified
subreddit and download them to a folder.

This fork goal is to create web gui,
so it can be paired with [hydrus](https://github.com/hydrusnetwork/hydrus).

other version can be found here

- original: [HoverHell/RedditImageGrab](https://github.com/HoverHell/RedditImageGrab)
- python3 fork: [jtara1/RedditImageGrab](https://github.com/jtara1/RedditImageGrab)

# Requirements:

 * Python3
 * Optional requirements: listed in setup.py under `extras_require`.


# Usage:

See `./redditdl.py --help` for uptodate details.

    redditdl.py [-h] [--multireddit] [--last l] [--score s] [--num n]
                     [--update] [--sfw] [--nsfw]
                     [--filename-format FILENAME_FORMAT] [--title-contain TEXT]
                     [--regex REGEX] [--verbose] [--skipAlbums]
                     [--mirror-gfycat] [--sort-type SORT_TYPE]
                     <subreddit> [<dest_file>]


Downloads files with specified extension from the specified subreddit.

positional arguments:

    <subreddit>           Subreddit name.
    <dest_file>           Dir to put downloaded files in.

optional arguments:

    -h, --help            show this help message and exit
    --multireddit         Take multirredit instead of subreddit as input. If so,
                        provide /user/m/multireddit-name as argument
    --last l              ID of the last downloaded file.
    --score s             Minimum score of images to download.
    --num n               Number of images to download.
    --update              Run until you encounter a file already downloaded.
    --sfw                 Download safe for work images only.
    --nsfw                Download NSFW images only.
    --regex REGEX         Use Python regex to filter based on title.
    --verbose             Enable verbose output.
    --skipAlbums          Skip all albums
    --mirror-gfycat       Download available mirror in gfycat.com.
    --filename-format FILENAME_FORMAT
                        Specify filename format: reddit (default), title or
                        url
    --sort-type         Sort the subreddit.


# Installation

```bash
$ git clone https://github.com/rachmadaniHaryono/RedditImageGrab/tree/master
$ cd redditdownload
$ pip install .
$ # to install server app
$ pip install .[server]
```
or directly with pip

```
[sudo] pip install https://github.com/rachmadaniHaryono/RedditImageGrab/archive/master.zip
```


# Examples

An example of running this script to download images with a score
greater than 50 from the wallpaper sub-reddit into a folder called
wallpaper would be as follows:

    python redditdl.py wallpaper wallpaper --score 50

And to run the same query but only get new images you don't already
have, run the following:

    python redditdl.py wallpaper wallpaper --score 50 -update

For getting some nice pictures of cats in your catsfolder (wich will be created if it
doesn't exist yet) run:

    python redditdl.py cats ~/Pictures/catsfolder --score 1000 --num 5 --sfw --verbose

To download from certain thread, you can use thread id. The valid command are following:

    python redditdl.py --last 508k37 gaming

To download from multireddit from an user run:

    python redditdl.py someuser/m/some_multireddit


## Advanced Examples

Retrieve last 10 pics in the 'wallpaper' subreddit with the word
"sunset" in the title (note: case is ignored by (?i) predicate)

    python redditdl.py wallpaper sunsets --regex '(?i).*sunset.*' --num 10

Download top week post from subreddit 'animegifs' and use gfycat gif mirror (if available)

    python redditdl.py animegifs --sort-type topweek --mirror-gfycat



# Examples as Hydrus booru (alpha)

The following command will run the server on port 5004 with thread mode

```bash
redditdl-server run -p 5004 --with-threads
```

Import following hydrus' booru config (assuming the server is run on port 5004)

```yaml
!Booru
_advance_by_page_num: true
_image_data: '[link]'
_image_id: null
_name: rdl
_search_separator: +
_search_url: http://127.0.0.1:5004/?subreddit=%tags%&page=%index%
_tag_classnames_to_namespaces: {tag-json-source: source, tag-json-title: title}
_thumb_classname: details
```

## Sorting

Available sorting are following : hot, new, rising, controversial, top, gilded

'top' and 'controversial' sorting can also be extended using available
time limit extension (hour, day, week, month, year, all).

example : tophour, topweek, topweek, controversialhour, controversialweek etc
