.PHONY: typing

typing:
	docker build -t type-check-02 .
	docker run --rm -v "$(PWD)":/work -w /work type-check-02 tasks
