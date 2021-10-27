obucket=advana-data-zone/
oprefix=bronze/dakotatest/pdf/nfrcopy/

destbucket=${obucket}
destprefix=bronze/dakotatest/pdf/flatten3/
destext=".pdf"
aws s3 ls "s3://${obucket}${oprefix}" --recursive | awk '{$1=$2=$3=""; sub(/^[ \t]+/, ""); print $0}' | cat > flatten.txt

while read opath; do
 if [ "${opath: -1}" != "/" ]; then
  destname=$(echo $opath | sed "s#${oprefix}##g" | sed "s#/# #g")
  aws s3 cp "s3://${obucket}${opath}" "s3://${destbucket}${destprefix}${destname}${destext}";                                                                                                                                                                
 fi
done < flatten.txt