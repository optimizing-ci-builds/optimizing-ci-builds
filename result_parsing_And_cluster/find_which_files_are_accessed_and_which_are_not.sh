#!/bin/bash
#MavenTestCI
#remotes/origin/JSqlParser.1671859411
#remotes/origin/fabric-sdk-java.1672108464
#jv-fruit-shop.1672108464
#Algorithms.1671724402
#mooc-software-testing.1672101501
#git checkout -f  MavenTestCI.1670985148

if [[ $1 == "" || $2 == "" || $3 == "" ]]; then
    echo "give $1 (directory name)"
    echo "give $2 (Project name)"
    echo "give $3 (useful.csv)"
    exit
fi
currentDir=$(pwd)
if [ -f "$currentDir/Output/$2-never-accessed" ]; then
    rm "$currentDir/Output/$2-never-accessed"
fi

if [ -f "$currentDir/Output/$2-accessed" ]; then
    rm "$currentDir/Output/$2-accessed"
fi
dir_arr=($(cd $1 && printf -- '%s\n' */))
#$(find . -maxdepth 1 -type d -printf '%f\n')
cd $1
#echo "PWD= ${dir_arr}"
never_accessed_file_name_array=("cm_a.csv" "c_m_a.csv" "c_m__a.csv" "cm__a.csv"  "_cm_a.csv"  "_cm__a.csv.csv"  "_c_m_a.csv" "_c_m__a.csv" )
accessed_file_name_array=("cma.csv" "c_ma.csv" "_cma.csv"  "_c_ma.csv"  )

if [[ ! -d "$currentDir/Output" ]]; then
    mkdir "$currentDir/Output"
fi

for i in "${dir_arr[@]}"
do

    echo "==========$i ========== $(pwd)"
    if [[ "$i" =~ .*"checkout".* ]]; then
        echo "checkout found"
        continue
    elif [[ "$i" =~ .*"setup".* ]]; then
       echo "setup found"
       continue
    else
        for j in "${never_accessed_file_name_array[@]}"
        do
            #echo $i$j
            if [ -f $i$j ]; then
                echo "Found $i$j"
                cat "$i$j" >> "$currentDir/Output/$2-never-accessed"
            else 
                echo "Not Found"
            fi
        done

        for k in "${accessed_file_name_array[@]}"
        do
            if [ -f $i$k ]; then
                echo "pwd =$(pwd)"
                echo $i$k
                cat "$i$k" >> "$currentDir/Output/$2-accessed"
            fi
        done

    fi
    #if [[ $i != "." ]]; then
    #fi
done

cat "$currentDir/Output/$2-never-accessed" | cut -d',' -f2 > "$currentDir/tmp1"
cat "$currentDir/tmp1" | sort | uniq > "$currentDir/tmp"
cp "$currentDir/tmp" "$currentDir/Output/$2-never-accessed" 
rm "$currentDir/tmp1"
rm "$currentDir/tmp"

cat "$currentDir/Output/$2-accessed" | cut -d',' -f2 > "$currentDir/tmp-access"
cat "$currentDir/tmp-access" | sort | uniq > "$currentDir/tmp-access1"
cp "$currentDir/tmp-access1" "$currentDir/Output/$2-accessed" 

rm "$currentDir/tmp-access1"
rm "$currentDir/tmp-access"

comm -13 <(sort -u "$currentDir/Output/$2-never-accessed") <(sort -u  "$currentDir/Output/$2-never-accessed") >  "$currentDir/Output/$2-common"

### Process useful.csv
cd $currentDir
row_count=1
while read line
do
    if [[ ${row_count} -gt 1 ]]; then
        file_name=$(echo $line | cut -d',' -f2)
        echo $file_name >>  "$currentDir/Output/$2-useful" 
    fi
    row_count=$((row_count+1))
done < $3
