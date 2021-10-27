# Important Moodle Tables

* m_course_sections
* m_files
* m_lesson_*


Files (e.g. PDF, h5p) are inside of 
`/var/www/moodledata/filedir/`

/var/www/moodledata/filedir/dd/3d/dd3dd21ad635e92be863608ee27d8647aab8e4d3

# How to export database from docker container
sudo mysqldump --user root --port 3306 --password --host 127.0.0.1 --skip-extended-insert --column-statistics=0 --compact moodle > mysql_dump.sql