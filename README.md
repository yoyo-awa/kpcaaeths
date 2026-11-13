# Kpcaaeths

[Click me to the wiki](https://esolangs.org/wiki/Kpcaaeths)

## Usage

Download `main.py`, then run:

```
python main.py <file.kpc>
```

Example:

```
python main.py examples/helloworld.kpc
```

## Example

`examples/helloworld.kpc`:

```
mk 0;
sto *0 10;
mk 1;
len *1 14;
sto *1 72;
sto *1 101;
sto *1 108;
sto *1 108;
sto *1 111;
sto *1 44;
sto *1 32;
sto *1 87;
sto *1 111;
sto *1 114;
sto *1 108;
sto *1 100;
sto *1 33;
sto *1 10;
loa *0;
giz 28;
loa *1;
psh 0;
op;
loa *0;
psh 1;
sub;
sfc *0;
gto 18;
```

Outputs `Hello, World!` ten times.