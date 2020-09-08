pip3 install setuptools 
pip3 install pyside2 psycopg2-binary pyserial matplotlib requests

echo "Downloading and extracting PostgreSQL binaries. This may take a while..."

python3 download.py

echo "Creating database from base template."

mkdir ./postgres/pgsql/cluster

./postgres/pgsql/bin/initdb -D ./postgres/pgsql/cluster
./postgres/pgsql/bin/pg_ctl start -D ./postgres/pgsql/cluster -l ./postgres/pgsql/log.txt
./postgres/pgsql/bin/psql postgres -c "CREATE ROLE teleuser WITH PASSWORD 'teleuser'"
./postgres/pgsql/bin/psql postgres -c "ALTER ROLE teleuser WITH LOGIN"

./postgres/pgsql/bin/createdb telemetry -O teleuser
./postgres/pgsql/bin/psql telemetry < ./postgres/backup/init.bak
./postgres/pgsql/bin/pg_ctl stop -D ./postgres/pgsql/cluster

chmod +x dbtools.sh
chmod +x visualizer.sh

read -p "Setup finished. Press any key to continue..."
