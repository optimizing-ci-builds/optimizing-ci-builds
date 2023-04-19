#!/bin/bash
if [[ $1 == "" ]]; then
    echo "give the csv name (e.g., ../../result_parsing_And_cluster/Unused_clusters_info.csv)"
    exit
fi

currentDir=$(pwd)
header=true
while read line
do 
    if [ "$header" = false ]; then 
        proj_name=$(echo $line | cut -d',' -f1)
        workflow_file=$(echo $line | cut -d',' -f2)
        unused_dirs=$(echo $line | cut -d',' -f4)
        git clone "git@github.com:optimizing-ci-builds/$proj_name" "../projects/$proj_name"
        ###############FIND EFFECTIVE POM#################
        cd "../projects/$proj_name"
        java_version=$(grep -i "java-version" $workflow_file  | head -1 | cut -d':' -f2 )
        java_version="${java_version//\'/}"
        echo $java_version

        if [[ "$java_version" == *"17"* ]]; then
            echo "JAVA -17"
            export JAVA_HOME=/usr/lib/jvm/java-1.17.0-openjdk-amd64/
        elif [[ "$java_version" == *"11"* ]]; then
            echo "JAVA -11"
            export JAVA_HOME=/usr/lib/jvm/java-1.11.0-openjdk-amd64/
        elif [[ "$java_version" == *"8"* ]]; then
            export JAVA_HOME=/usr/lib/jvm/java-1.8.0-openjdk-amd64/
            echo "JAVA -8"
            echo $JAVA_HOME
        fi
        mvn org.apache.maven.plugins:maven-help-plugin:3.4.0:effective-pom -Doutput=effective-pom.xml
        cd $currentDir
        #Find each unused dir one by one
        tildeCount=$(echo ${unused_dirs} | tr -cd ~ | wc -c)
        for (( i=1; i<=${tildeCount}; i++))
        do
            unnecessary_dir=$(echo "$unused_dirs" | cut -d'~' -f$i)
            echo $unnecessary_dir
            semicolon_found_indicates_file=$(echo  $unnecessary_dir | grep ";" | wc -l)
            if [[ $semicolon_found_indicates_file -gt 0 ]]; then
                python3 find_plugin_corpus.py "../projects/$proj_name/effective-pom.xml" ${unnecessary_dir}
                exit
            fi
        done
    fi
    header=false
done < $1

