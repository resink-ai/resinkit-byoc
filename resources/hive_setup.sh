#!/bin/bash
# shellcheck disable=SC2086,SC2155

# This script sets up the Hive Metastore on a Debian-based system.

debian_install_hadoop_flink_iceberg() {

    # Install flink-hive connector
    mkdir -p /opt/hive-conf
    cat <<EOL > /opt/hive-conf/hive-site.xml
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<configuration>
  <property>
    <name>hive.metastore.uris</name>
    <value>thrift://localhost:9083</value>
    <description>URI for client to contact metastore server</description>
  </property>
  <!-- Add other necessary Hive configuration properties here -->
</configuration>
EOL



    wget https://repo.maven.apache.org/maven2/org/apache/iceberg/iceberg-flink-runtime-1.19/1.8.1/iceberg-flink-runtime-1.19-1.8.1.jar

    # HADOOP_HOME is your hadoop root directory after unpack the binary package.
    export HADOOP_CLASSPATH=$($HADOOP_HOME/bin/hadoop classpath)

    ICEBERG_VERSION=1.8.1
    MAVEN_URL=https://repo1.maven.org/maven2
    ICEBERG_MAVEN_URL=${MAVEN_URL}/org/apache/iceberg
    ICEBERG_PACKAGE=iceberg-flink-runtime
    FLINK_VERSION_MAJOR=1.19
    wget ${ICEBERG_MAVEN_URL}/${ICEBERG_PACKAGE}-${FLINK_VERSION_MAJOR}/${ICEBERG_VERSION}/${ICEBERG_PACKAGE}-${FLINK_VERSION_MAJOR}-${ICEBERG_VERSION}.jar -P lib/

    HIVE_VERSION=2.3.9
    SCALA_VERSION=2.12
    FLINK_VERSION=1.20.0
    FLINK_CONNECTOR_URL=${MAVEN_URL}/org/apache/flink
    FLINK_CONNECTOR_PACKAGE=flink-sql-connector-hive
    wget ${FLINK_CONNECTOR_URL}/${FLINK_CONNECTOR_PACKAGE}-${HIVE_VERSION}_${SCALA_VERSION}/${FLINK_VERSION}/${FLINK_CONNECTOR_PACKAGE}-${HIVE_VERSION}_${SCALA_VERSION}-${FLINK_VERSION}.jar

    ./bin/sql-client.sh embedded shell
}

debian_download_and_setup_hadoop() {
    # Download and install Hadoop
    wget https://downloads.apache.org/hadoop/common/hadoop-3.3.6/hadoop-3.3.6.tar.gz
    tar -xzf hadoop-3.3.6.tar.gz
    mv hadoop-3.3.6 /opt/hadoop
    rm hadoop-3.3.6.tar.gz

    # Set up environment variables
    cat <<EOL >> /etc/profile.d/hadoop.sh

export HADOOP_HOME=/opt/hadoop
export HADOOP_INSTALL=$HADOOP_HOME
export HADOOP_MAPRED_HOME=$HADOOP_HOME
export HADOOP_COMMON_HOME=$HADOOP_HOME
export HADOOP_HDFS_HOME=$HADOOP_HOME
export HADOOP_YARN_HOME=$HADOOP_HOME
export HADOOP_COMMON_LIB_NATIVE_DIR=$HADOOP_HOME/lib/native
export PATH=$PATH:$HADOOP_HOME/sbin:$HADOOP_HOME/bin
export HADOOP_OPTS="-Djava.library.path=$HADOOP_HOME/lib/native"

EOL

    source /etc/profile.d/hadoop.sh
    # Edit core-site.xml:
    cat <<EOL > /opt/hadoop/etc/hadoop/core-site.xml
<configuration>
    <property>
        <name>fs.defaultFS</name>
        <value>hdfs://localhost:9000</value>
    </property>
    <property>
        <name>hadoop.tmp.dir</name>
        <value>/opt/hadoop/tmp</value>
    </property>
</configuration>

EOL

    # make folders
    mkdir -p /opt/hadoop/hdfs/namenode
    mkdir -p /opt/hadoop/hdfs/datanode

    # Edit hdfs-site.xml:
    cat <<EOL > /opt/hadoop/etc/hadoop/hdfs-site.xml
<configuration>
    <property>
        <name>dfs.replication</name>
        <value>1</value>
    </property>
    <property>
        <name>dfs.namenode.name.dir</name>
        <value>/opt/hadoop/hdfs/namenode</value>
    </property>
    <property>
        <name>dfs.datanode.data.dir</name>
        <value>/opt/hadoop/hdfs/datanode</value>
    </property>
</configuration>

EOL

    # mapred-site.xml
    cat <<EOL > /opt/hadoop/etc/hadoop/mapred-site.xml
<configuration>
    <property>
        <name>dfs.replication</name>
        <value>1</value>
    </property>
    <property>
        <name>dfs.namenode.name.dir</name>
        <value>/opt/hadoop/hdfs/namenode</value>
    </property>
    <property>
        <name>dfs.datanode.data.dir</name>
        <value>/opt/hadoop/hdfs/datanode</value>
    </property>
</configuration>
EOL


    # Edit yarn-site.xml:
    cat <<EOL > /opt/hadoop/etc/hadoop/yarn-site.xml
<configuration>
    <property>
        <name>yarn.nodemanager.aux-services</name>
        <value>mapreduce_shuffle</value>
    </property>
    <property>
        <name>yarn.nodemanager.aux-services.mapreduce.shuffle.class</name>
        <value>org.apache.hadoop.mapred.ShuffleHandler</value>
    </property>
</configuration>
EOL

    # Format the namenode
    /opt/hadoop/bin/hdfs namenode -format

    # Start HDFS
    /opt/hadoop/sbin/start-dfs.sh

    # Start YARN
    /opt/hadoop/sbin/start-yarn.sh

    # Check if Hadoop is running
    jps
}

debian_download_and_setup_hive_metastore() {
    # Download and install Hive Metastore
    wget https://downloads.apache.org/hive/hive-standalone-metastore-3.0.0/hive-standalone-metastore-3.0.0-bin.tar.gz
    tar -xzf hive-standalone-metastore-3.0.0-bin.tar.gz
    mv hive-standalone-metastore-3.0.0-bin /opt/hive
    rm hive-standalone-metastore-3.0.0-bin.tar.gz

    # setup metastore-site.xml
    cat <<EOL > /opt/hive/conf/metastore-site.xml
<configuration>
  <property>
    <name>metastore.thrift.uris</name>
    <value>thrift://localhost:9083</value>
  </property>
  <property>
    <name>metastore.task.threads.always</name>
    <value>org.apache.hadoop.hive.metastore.events.EventCleanerTask</value>
  </property>
  <property>
    <name>metastore.expression.proxy</name>
    <value>org.apache.hadoop.hive.metastore.DefaultPartitionExpressionProxy</value>
  </property>
  <property>
    <name>javax.jdo.option.ConnectionURL</name>
    <value>jdbc:mysql://localhost/metastore_db?createDatabaseIfNotExist=true</value>
  </property>
  <property>
    <name>javax.jdo.option.ConnectionDriverName</name>
    <value>com.mysql.jdbc.Driver</value>
  </property>
  <property>
    <name>javax.jdo.option.ConnectionUserName</name>
    <value>hive</value>
  </property>
  <property>
    <name>javax.jdo.option.ConnectionPassword</name>
    <value>cnk8_</value>
  </property>
</configuration>

EOL

    # Create the Hive Metastore database
    # mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS metastore_db;"
    # mysql -u root -p -e "CREATE USER 'hive'@'localhost' IDENTIFIED BY 'hivepassword';"
    # mysql -u root -p -e "GRANT ALL PRIVILEGES ON metastore_db.* TO 'hive'@'localhost';"
    # mysql -u root -p -e "FLUSH PRIVILEGES;"

    # Initialize the Metastore schema
    /opt/hive/bin/schematool -dbType mysql -initSchema

    # Start the Hive Metastore service
    nohup /opt/hive/bin/hive --service metastore > /var/log/hive/hivemetastore.log 2>&1 &
}
