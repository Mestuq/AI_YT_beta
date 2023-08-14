# TagsAI

![](https://github.com/Mestuq/AI_YT_test/blob/main/www/static/logo.png)

**Flask (Python) website for Machine Learning Youtube tags.**

1. Write topic of your video
2. Wait...
3. Boom! Ready tags to copy, perfect for your videos.

## Info

This model is pretty slow. Need probably more than an hour per query to generate a raport.

I know ChatGPT, can generate tags much faster and have much bigger database, but even of small accuracy of this project, from my expirience this project generates a little bit better result in views for me than from ChatGPT.
Accuracy is poor, because i dont have enaught information to work with. My data is really limited. Youtube studio have options to load clickrate, impressions etc. but this data is hidden from public.

Because of that I don't think that, there are bad results, considering that the "tags" is not most important indicator of video popularity.

I prefere to consider both models during choosing tags to paste into my videos, because i dont know of how exactly Youtube alghoritm works.

## Steps

1. **Program asks user for search query.**
   Program will looks for youtube channels with similar topics. (Will add to channels list all thats uploaders info from videos that will appear after searching that text into youtube search in given pages number)
2. **Download video info (uploader name, views and list of tags).**
   For each channel will be downloaded given number of videos info (or less, if channel doesnt have that many videos).
   This is taking the most of loading time, because for better analysis we recommend to download at least 1000 videos infos.
3. **Select channels.**
   Select which channels will be considered in a training set.
4. **Preparing data.**

- Generate a boolean table (videos in rows and tags (with channel name in considiration because every channel have some sort of regular audiences) as columns).
- Delete rows (videos) with to small amount of tags (rows with too small information to predict results)
- Delete columns bearly used. (To small amout of videos uses this tag, so predicting result from this tags are uncertain)
- Removing outliners points.

5. **Creating model**
   In this project i use two models (For now. I planning to add more models later)

- Standard Logistic Regression
- Random Forest Classifier

6. **Cross-Validation (Accuracy)**
   I am using LOOCV (Leave-One-Out Cross-Validation). It is slow method, but I prefer this method because our sort of data is very specific (Variables may occur too infrequently and if we split a set into test and training we can get improper results, even more so
   for information about the owner of the video)
7. **Suggested tags**
   These models gives us the coefficient (or feature importances) numbers that we can use to predict tags that will give us the most of views. Sorted from the higher impact.
8. **Save your favorite tags**
   Option for export your result for later.

## Installing

### Pyinstaller

I am building application for my releases, so all you need to do is to download them and run exe.

But if you want to build it on your own, then run following commands:

```
cd www
pyinstaller StandaloneVersion.spec
```

## Via docker

Run following line

```
docker build -t tagsai:mestuq .
docker run -p 5000:5000 --name TagsAI tagsai:mestuq
```

Website is avalible in http://127.0.0.1:5000/ .

### Via python script

Install required

```
pip install -r requirements.txt
```

Or use lock files avalible in "Lock files" folder.

```
pipenv shell
pipenv install --ignore-pipfile
```

Then run

```
python "www/main.py"
```

Website is avalible in http://127.0.0.1:5000/ .

## Future plans

- Currently im not considering "date of uploading" as a predictor.
- Looking for faster method for downloading Youtube Data. (Currently using yt_dlp, because it is free), but planning Youtube API in the future.
