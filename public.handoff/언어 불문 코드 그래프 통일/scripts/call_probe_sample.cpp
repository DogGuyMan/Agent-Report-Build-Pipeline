struct Base { virtual int draw(int x) { return x; } virtual ~Base() = default; };
struct Derived : Base { int draw(int x) override { return helper(x) + 1; } static int helper(int v) { return v * 2; } };
template <typename T> T twice(T v) { return v + v; }
int free_fn(Base& b) { auto f = [&](int k) { return b.draw(k); }; return f(1) + twice(2) + Derived::helper(3); }
int main() { Derived d; return free_fn(d); }
