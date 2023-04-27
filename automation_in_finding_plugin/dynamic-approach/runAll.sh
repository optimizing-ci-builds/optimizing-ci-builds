#!/bin/bash
if [[ $1 == "" ]]; then
    #echo "give the csv name (e.g., ../../result_parsing_And_cluster/Unused_clusters_info.csv)"
    echo "give the csv name (e.g., ../static-approach/Result.csv)"
    exit
fi

currentDir=$(pwd)
header=true

logs="logs"
if [ ! -d "$logs" ]; then
    mkdir "$logs"
fi

while read line  # looping through each of the unnnecessary directory
do 
    plugin_which_generates_unused_dir_found=0
    proj_name=$(echo $line | cut -d',' -f1)
    workflow_file=$(echo $line | cut -d',' -f2)
    java_version=$(echo $line | cut -d',' -f3)
    mvn_command=$(echo $line | cut -d',' -f4)
    unused_csv_file=$(echo $line | cut -d',' -f5)
    unused_dir=$(echo $line | cut -d',' -f6)
    plugins=($(echo $line | sed -e 's/.*{\(.*\)}.*/\1/' | tr -d ' ' | tr ',' '\n' |  sed -e 's/"\([^"]*\)":/\1=/g' | cut -d'=' -f1)) # all the plugins that are found by static approach
    echo ${plugins[@]}
    if [[ "$unused_dir" == "target/surefire-reports/" ]]; then
        #echo "Not-Running-Dynamic=>$unused_csv_file,$workflow_file,$unused_dir,-DdisableXmlReport=true" >> "$currentDir/Result.csv"
        continue
    elif [[ "$unused_dir" == "target/maven-status/" ]]; then
        #echo "Not-Running-Dynamic=>$unused_csv_file,$workflow_file,$unused_dir,from-some-compiler-plugin" >> "$currentDir/Result.csv"
        continue
    fi

    git clone "git@github.com:optimizing-ci-builds/$proj_name" "../projects/$proj_name"
    ###############FIND EFFECTIVE POM#################
    cd "../projects/$proj_name"
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
    cp "effective-pom.xml" "effective-pom_org.xml"
    already_run_plugin=[]
    #search for the plugin that our static analysis suggests
    for plugin in ${plugins[@]}; do 
        #1. split the plugin with # and get  groupid and artifactid
        IFS="#" read -ra varArray <<< "$plugin"
        #echo ${varArray[0]}
        groupId=${varArray[0]}
        artifactId=${varArray[1]}

        #range_build_plugins_from_effective_pom=($(awk '/<build>/,/<\/build>/ {if(/<plugins>/) {start=NR}; if(/<\/plugins>/) {print start; print NR; exit}}' effective-pom.xml))

        range_build_plugins_from_effective_pom=($(awk '/<build>/,/<\/build>/ {
    if(/<plugins>/) {
        if(!pMgmt) {start=NR}
    }
    if(/<\/plugins>/) {
        if(!pMgmt) {print start; print NR; exit}
    }
    if(/<pluginManagement>/) {
        pMgmt=1
    }
    if(/<\/pluginManagement>/) {
        pMgmt=0
    }
}' effective-pom.xml))

        Start_range="${range_build_plugins_from_effective_pom[0]}"
        end_range="${range_build_plugins_from_effective_pom[1]}"
        sed -n "$Start_range,${end_range}p" effective-pom.xml | awk -v adj=$Start_range '{printf("%-5d%s\n", NR-1+adj, $0)}' > tmp.xml

        ## Now we need to know the plugin line number that we want to disable. ss_plugin_line will store the line number of the plugin of the given groupId and artifactId
        groupId_line_arr=($(grep -n ">$groupId</" "tmp.xml" | cut -d':' -f2 | cut -d' ' -f1 )) #assuming that groupId comes first. even if it does not come, that will not be a problem because we are using variable to store the name. Here I am taking the first matched groupId. I can work here to comment other matched locations. Sometimes we may get a grpId more that 1 time
        echo $groupId_line
        for groupId_line in ${groupId_line_arr[@]}; do 
            if [[ -z $groupId_line ]];then 
                continue
            fi
            
            if [[ ! -z $artifactId ]]; then # because sometime artifactid might not exists
                artifactId_line=$(grep -n ">$artifactId</" "tmp.xml" | cut -d':' -f2 | cut -d' ' -f1)
                gg=$((groupId_line + 1))
                if [[ $gg -eq $artifactId_line ]]; then
                    ss_plugin_line=$((groupId_line - 1))
                    break
                elif [[ $gg -eq $artifactId_line ]]; then #indicates theese groupId and artifactId comes one by another
                    ss_plugin_line=$((artifactId_line - 1))
                    break
                else
                    continue # This means that artifactId doesn't match
                fi
            else
                echo "HI $groupId_line ************"
                ss_plugin_line=$((groupId_line - 1)) 
                break
            fi
        
        done
        #echo "gropLine=$groupId_line" 
        #plugin_start_line=$((groupId_line -1)) #plugin's starting line  
        #echo $plugin_start_line
        plugin_relative_end=$(sed -n "$ss_plugin_line,\$p" effective-pom.xml | grep -n "</plugin>" | head -1 | cut -d':' -f1)
        echo "rel=$plugin_relative_end"
        plugin_absolute_end="$((plugin_relative_end + ss_plugin_line))"
        echo "plugin's start and end locations="
        echo $ss_plugin_line
        echo "abs=$plugin_absolute_end"
        how_far_plugin_end_from_this_given_line=$(sed -n "$ss_plugin_line,\$p" effective-pom.xml | grep -n "</plugin>" | head -1 | cut -d':' -f1)
        echo "END="$how_far_plugin_end_from_this_given_line
        plugin_end=$((how_far_plugin_end_from_this_given_line + ss_plugin_line -1))
        se="${ss_plugin_line}#${plugin_absolute_end}"
        echo $se
        already_run_plugin+=("$se")
        sed -i "${ss_plugin_line},${plugin_end} {
        /^\s*<!--/b   # skip lines that are already commented
        s/^/<!-- /    # add comment tag to beginning of line
        s/$/ -->/     # add comment tag to end of line
        }" effective-pom.xml
        echo "start=$ss_plugin_line, end=$plugin_end, $workflow_file, $java_version"
        #now run the mvn command  
        last_level_dir=$(echo $unused_dir | rev | cut -d'/' -f2 | rev)

        mvn clean
        mvn -version 
        echo $JAVA_HOME
        echo ${mvn_command} 
        ${mvn_command} --file effective-pom.xml > "$currentDir/$logs/log_${last_level_dir}_${ss_plugin_line}.txt"
        #echo $last_level_dir
        #check if the unused directory exists or not (find -name ..), if no directory found. we will report the plugin name
        if [ "$(find "target" -name $last_level_dir | wc -l)" -gt 0 ]; then # directory found
            echo "Still-exists"
            echo "FROM STATIC=>$unused_dir,$unused_csv_file,$workflow_file,$unused_dir,$groupId#$artifactId" >> "$currentDir/Found-Dir.csv"
            cp "effective-pom_org.xml" "effective-pom.xml"
        else
            echo "FROM STATIC=>$unused_dir,$unused_csv_file,$workflow_file,$unused_dir,$groupId#$artifactId" >> "$currentDir/Result.csv"
            cp "effective-pom_org.xml" "effective-pom.xml"
            plugin_which_generates_unused_dir_found=1
            break
        fi
        #exit 
    done

    if [ ${plugin_which_generates_unused_dir_found} -eq 0 ]; then # IF we do not find any plugin which generates the unnecessary dir from the above code 
        #1.2 IF we need to search for all plugins one by one
        # Collecting all plugins start and ending 
        range_build_plugins=($(awk '/<build>/,/<\/build>/ {
    if(/<plugins>/) {
        if(!pMgmt) {start=NR}
    }
    if(/<\/plugins>/) {
        if(!pMgmt) {print start; print NR; exit}
    }
    if(/<pluginManagement>/) {
        pMgmt=1
    }
    if(/<\/pluginManagement>/) {
        pMgmt=0
    }
}' effective-pom.xml)) #this one is ignoring the plugins if it belongs to pluginManagement

        Start_range="${range_build_plugins[0]}"
        end_range="${range_build_plugins[1]}"
        sed -n "$Start_range,${end_range}p" effective-pom.xml | awk -v adj=$Start_range '{printf("%-5d%s\n", NR-1+adj, $0)}' > tmp.xml
        plugin_starting_loc=($(grep -n "<plugin>" "tmp.xml" | cut -d':' -f2 | cut -d' ' -f1)) #becayse after greping we get 2:79 <plugin> 98:175 <plugin>". So, we need to extract 79 because this is the original line in the pom.xml
        echo "starting loc=${plugin_starting_loc[@]}" # all plugin starting tag
        for plugin_start in ${plugin_starting_loc[@]}
        do
            how_far_plugin_end_from_this_given_line=$(sed -n "$plugin_start,\$p" effective-pom.xml | grep -n "</plugin>" | head -1 | cut -d':' -f1)
            plugin_end=$((how_far_plugin_end_from_this_given_line + plugin_start -1))
            st_end="$plugin_start#$plugin_end"
            if [[ " ${already_run_plugin[*]} " == *" $st_end "* ]]; then
                echo "aleady visited"
                continue
            fi

            sed -i "${plugin_start},${plugin_end} {
            /^\s*<!--/b   # skip lines that are already commented
            s/^/<!-- /    # add comment tag to beginning of line
            s/$/ -->/     # add comment tag to end of line
            }" effective-pom.xml
            echo "start=$plugin_start, end=$plugin_end, $workflow_file, $java_version"

            last_level_dir=$(echo $unused_dir | rev | cut -d'/' -f2 | rev)
            groupId_index=$((Start_range + 2))
            artifact_index=$((Start_range + 3))
            groupId=$(sed -n "${groupId_index}{s/.*>\(.*\)<.*/\1/p;q;}" effective-pom_org.xml)
            artifactId=$(sed -n "${artifact_index}{s/.*>\(.*\)<.*/\1/p;q;}" effective-pom_org.xml)

            #now run the mvn command  
            mvn clean
            mvn -version
            echo $JAVA_HOME
            echo ${mvn_command} 
            ${mvn_command} --file effective-pom.xml > "$currentDir/$logs/log_${last_level_dir}_${plugin_start}.txt"

            if [ -n "$(find "target" -name $last_level_dir)" ]; then 
                echo "Still found"
                echo "$unused_dir,$unused_csv_file,$workflow_file,$unused_dir,$groupId#$artifactId" >> "$currentDir/Found-Dir.csv"
                cp "effective-pom_org.xml" "effective-pom.xml"
            else
                echo "not-found"
                echo $Start_range
                echo $end_range
                #find the plugin name
                echo "$unused_dir,$unused_csv_file,$workflow_file,$unused_dir,$groupId#$artifactId" >> "$currentDir/Result.csv"
                cp "effective-pom_org.xml" "effective-pom.xml"
                break
            fi
        done
    fi
    exit
done < $1

