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
        java_version=$(echo $line | cut -d',' -f3)
        mvn_command=$(echo $line | cut -d',' -f4)
        unused_dirs=$(echo $line | cut -d',' -f6)

        git clone "git@github.com:optimizing-ci-builds/$proj_name" "../projects/$proj_name"
        ###############FIND EFFECTIVE POM#################
        cd "../projects/$proj_name"
        #java_version=$(grep -i "java-version" $workflow_file  | head -1 | cut -d':' -f2 )
        #java_version="${java_version//\'/}"
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
        
        cp "pom.xml" "pom_org.xml"
        tildeCount=$(echo ${unused_dirs} | tr -cd '~' | wc -c) #multiple unused directory might exists
        echo ${unused_dirs} ${tildeCount}
        for (( i=1; i<=${tildeCount}; i++))
        do
            unnecessary_dir=$(echo "$unused_dirs" | cut -d'~' -f$i)
            semicolon_found_indicates_file=$(echo  $unnecessary_dir | grep ";" | wc -l)
            if [[ $semicolon_found_indicates_file -eq 0 ]]; then
                range_build_plugins=($(awk '/<build>/,/<\/build>/ {if(/<plugins>/) {start=NR}; if(/<\/plugins>/) {print start; print NR; exit}}' pom.xml))
                Start_range="${range_build_plugins[0]}"
                end_range="${range_build_plugins[1]}"
                sed -n "$Start_range,${end_range}p" pom.xml | awk -v adj=$Start_range '{printf("%-5d%s\n", NR-1+adj, $0)}' > tmp.xml
                plugin_starting_loc=($(grep -n "<plugin>" "tmp.xml" | cut -d':' -f2 | cut -d' ' -f1)) #becayse after greping we get 2:79 <plugin> 98:175 <plugin>". So, we need to extract 79 because this is the original line in the pom.xml
                echo "starting loc=${plugin_starting_loc[@]}"
                for plugin_start in ${plugin_starting_loc[@]}
                do
                    how_far_plugin_end_from_this_given_line=$(sed -n "$plugin_start,\$p" pom.xml | grep -n "</plugin>" | head -1 | cut -d':' -f1)
                    plugin_end=$((how_far_plugin_end_from_this_given_line + plugin_start -1))
                    sed -i "${plugin_start},${plugin_end} {
                    /^\s*<!--/b   # skip lines that are already commented
                    s/^/<!-- /    # add comment tag to beginning of line
                    s/$/ -->/     # add comment tag to end of line
                    }" pom.xml
                    echo "start=$plugin_start, end=$plugin_end, $workflow_file, $java_version"
                    #now run the mvn command  
                    last_level_dir=$(echo $unnecessary_dir | rev | cut -d'/' -f2 | rev)
                    mvn clean
                    ${mvn_command} > "log_${last_level_dir}_${plugin_start}.txt"
                    #echo $last_level_dir
                    #check if the unused directory exists or not (find -name ..), if no directory found. we will report the plugin name
                    if [ -n "$(find "target/" -name $last_level_dir)" ]; then 
                        echo "found"
                        cp "pom_org.xml" "pom.xml"
                    else
                        echo "not-found"
                        echo $Start_range
                        echo $end_range
                        groupId_index=$((Start_range + 1))
                        artifactId_index=$((Start_range + 1))
                        groupId=$(sed -n "${groupId_index}{s/.*>\(.*\)<.*/\1/p;q;}" pom_org.xml)
                        echo $groupId
                        artifactId=$(sed -n "${artifact_index}{s/.*>\(.*\)<.*/\1/p;q;}" pom_org.xml)
                        echo $artifactId
                        #find the plugin name
                        echo "$unnecessary_dir,$groupId#$artifactId" >> "$currentDir/Result.csv"
                        cp "pom_org.xml" "pom.xml"
                        break
                    fi
                done
                #exit
            fi
        done
        #exit 
    fi
    header=false
done < $1

