FOLDER=20-newsgroup
TAR=pyserini-20newsgroup.tar.gz

wget https://www.dropbox.com/s/b05esbt406g2y7c/${TAR}
rm -rf ${FOLDER}
mkdir -p ${FOLDER}
tar xvzf ${TAR} -C ${FOLDER}
rm ${TAR}
