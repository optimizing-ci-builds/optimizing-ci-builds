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
        
        range_build_plugins=($(awk '/<build>/,/<\/build>/ {if(/<plugins>/) {start=NR}; if(/<\/plugins>/) {print start; print NR; exit}}' pom.xml))
        echo ${range_build_plugins[@]}
        Start_range="${range_build_plugins[0]}"
        echo $"START range=$Start_range"
        end_range="${range_build_plugins[1]}"
        #build_line=$(grep -n '<build>' pom.xml | cut -d: -f1 | head -1)
        sed -n "$Start_range,${end_range}p" pom.xml | awk -v adj=$Start_range '{printf("%-5d%s\n", NR-1+adj, $0)}' > tmp.xml
        plugin_starting_loc=($(grep -n "<plugin>" "tmp.xml" | cut -d':' -f2 | cut -d' ' -f1)) #becayse after greping we get 2:79 <plugin> 98:175 <plugin>". So, we need to extract 79 because this is the original line in the pom.xml
        echo "starting loc=${plugin_starting_loc[@]}"
        echo $(pwd)
        cp "pom.xml" "pom_org.xml"
        for plugin_start in ${plugin_starting_loc[@]}
        do
            how_far_plugin_end_from_this_given_line=$(sed -n "$plugin_start,\$p" pom.xml | grep -n "</plugin>" | head -1 | cut -d':' -f1)
            plugin_end=$((how_far_plugin_end_from_this_given_line + plugin_start -1))
            #sed -i "${plugin_start},${plugin_end}s/^/<!-- /; ${plugin_start},${plugin_end}s/$/ -->/" pom.xml
            sed -i "${plugin_start},${plugin_end} {
            /^\s*<!--/b   # skip lines that are already commented
            s/^/<!-- /    # add comment tag to beginning of line
            s/$/ -->/     # add comment tag to end of line
            }" pom.xml
            echo "start=$plugin_start, end=$plugin_end, pppppppppp"
            #now run the mvn command  
            #check if the unused directory exists or not (find -name ..), if no directory found. we will report the plugin name
            if [ -n "$(find "target/" -name $unused-dir)" ]; then 
                echo "found"
                cp "pom_org.xml" "pom.xml"
            else
                echo "no-found"
                #returning the plugin name
            fi
            #exit
        done

        
        #$mvn_command  > "$currentDir/log" #whole command that they originally used
        #sed -n '/<plugins>/,/<\/plugins>/p' pom.xml > "tmp.xml"
        #sed -n "1,${profile_start}p; ${profile_end},\$p; /<plugins>/,/<\/plugins>/p" pom.xml > "tmp.xml"
        #sed -n "1,${profile_start}p; ${profile_end},\$p; /<profiles>/,/<\/profiles>/b; /<plugins>/,/<\/plugins>/p" pom.xml > "tmp.xml"
        #sed "${profile_start},${profile_end}c\\" pom.xml > "tmp.xml"
        #sed '/<profiles>/,/<\/profiles>/d' pom.xml > "tmp.xml"
        


        exit
        input=$(grep -n "<plugin>" tmp.xml)
        #input="2: <plugin> 98: <plugin> 152: <plugin> 175: <plugin> 214: <plugin> 254: <plugin> 267: <plugin> 296: <plugin> 325: <plugin> 341: <plugin> 346: <plugin> 356: <plugin> 367: <plugin> 388: <plugin> 400: <plugin> 412: <plugin>"
        #IFS=' ' read -ra array <<< "$(echo "$input" | cut -d ':' -f1)"
        #IFS=' ' read -ra array <<< "$(echo "$input" | cut -f1 -d' ')"
        #echo "${array[@]}"
        exit
        IFS=' ' read -ra arr <<< "$(echo "$input" | cut -d ':' -f1)"
        echo ${arr[@]}
        for plugin in "${arr[@]}"; do
          #echo "$plugin"
          line=$(echo $plugin | cut -d':' -f1)
          echo "LLL=$line"
          sed -n "$line,+2p" tmp.xml
          echo "HA HA"
          exit
        done
        exit
        if [[ -f effective-pom.xml ]]; then
            cd $currentDir
            #Find each unused dir one by one
            tildeCount=$(echo ${unused_dirs} | tr -cd '~' | wc -c)
            echo ${unused_dirs} ${tildeCount}
            for (( i=1; i<=${tildeCount}; i++))
            do
                unnecessary_dir=$(echo "$unused_dirs" | cut -d'~' -f$i)
                semicolon_found_indicates_file=$(echo  $unnecessary_dir | grep ";" | wc -l)
                #echo "Should be greater than 1=$semicolon_found_indicates_file"

                if [[ $semicolon_found_indicates_file -gt -1 ]]; then
                    #echo "UNU $unnecessary_dir"
                    echo -n "../projects/$proj_name/effective-pom.xml,${unnecessary_dir}," >> "$currentDir/Result.csv"
                    python3 find_plugin_corpus.py "../projects/$proj_name/effective-pom.xml" ${unnecessary_dir}
                    #echo "SHANTO*** ${unnecessary_dir}"
                    echo "" >> "$currentDir/Result.csv"
                    #exit
                fi
            done
        fi
        #exit
    fi
    header=false
done < $1

