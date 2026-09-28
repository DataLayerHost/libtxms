.PHONY: all test sanitize clean
all:
	cmake -S . -B build
	cmake --build build
test: all
	ctest --test-dir build --output-on-failure
sanitize:
	cmake -S . -B build-sanitize -DTXMS_SANITIZE=ON
	cmake --build build-sanitize
	ctest --test-dir build-sanitize --output-on-failure
clean:
	rm -rf build build-sanitize
