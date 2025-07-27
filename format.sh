isort backend/

flake8 backend/ | while read -r line; do
    file=$(echo "$line" | cut -d ':' -f 1)
    autopep8 --in-place --aggressive "$file"
done

flake8 backend/