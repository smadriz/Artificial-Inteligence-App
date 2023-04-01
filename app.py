from flask import Flask, render_template, request, redirect, url_for
import pymysql.cursors
from pysentimiento import SentimentAnalyzer

app = Flask(__name__)
analyzer = SentimentAnalyzer(lang="es")

# Database connection
def get_db_connection():
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='pass',
        database='tec_courses',
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection

@app.route('/')
def index():

    connection = get_db_connection()
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM courses")
        courses = cursor.fetchall()

    course_sentiments = []
    for course in courses:
        sentiment_counts = get_sentiment_counts(course["id"])
        
        total_comments = sum(sentiment_counts.values())
        if total_comments > 0:
            percentage_positive = (sentiment_counts["positive"] / total_comments) * 100
            percentage_negative = (sentiment_counts["negative"] / total_comments) * 100
            percentage_neutral = (sentiment_counts["neutral"] / total_comments) * 100
        else:
            percentage_positive = 0
            percentage_negative = 0
            percentage_neutral = 0

        sentiment_dict = {
            "positive": percentage_positive,
            "negative": percentage_negative,
            "neutral": percentage_neutral
        }

        course_sentiments.append(sentiment_dict)

    

    return render_template('index.html', courses=courses, course_sentiments=course_sentiments, zip=zip)




@app.route('/course/<int:course_id>', methods=['GET', 'POST'])
def course(course_id):
    connection = get_db_connection()

    if request.method == 'POST':
        comment = request.form['comment']
        sentiment = analyzer.predict(comment).output.lower()

        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO comments (course_id, content, sentiment) VALUES (%s, %s, %s)", (course_id, comment, sentiment))
            connection.commit()

        return redirect(url_for('course', course_id=course_id))

    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM courses WHERE id=%s", (course_id,))
        course = cursor.fetchone()
        cursor.execute("SELECT * FROM comments WHERE course_id=%s", (course_id,))
        comments = cursor.fetchall()

    return render_template('course.html', course=course, comments=comments)

def get_sentiment_counts(course_id):
    connection = get_db_connection()
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT sentiment, COUNT(*) as count FROM comments WHERE course_id = %s GROUP BY sentiment",
            (course_id,)
        )
        sentiment_counts = cursor.fetchall()

    sentiment_counts_dict = {"positive": 0, "negative": 0, "neutral": 0}
    for row in sentiment_counts:
        sentiment_label = row["sentiment"].lower()
        if sentiment_label in sentiment_counts_dict:
            sentiment_counts_dict[sentiment_label] += row["count"]
        elif sentiment_label == 'pos':
            sentiment_counts_dict['positive'] += row["count"]
        elif sentiment_label == 'neu':
            sentiment_counts_dict['neutral'] += row["count"]
        elif sentiment_label == 'neg':
            sentiment_counts_dict['negative'] += row["count"]

    return sentiment_counts_dict


if __name__ == '__main__':
    app.debug = True
    app.run()
    
