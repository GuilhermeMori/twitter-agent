#!/usr/bin/env python3
"""
Database Initialization Script
Executes migrations and seeds initial data in Supabase
"""

import os
import sys
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_supabase_client() -> Client:
    """Create Supabase client"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment")
    
    return create_client(url, key)

def execute_sql_file(client: Client, file_path: Path) -> None:
    """Execute SQL file in Supabase"""
    print(f"📄 Executando: {file_path.name}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    try:
        # Execute SQL via RPC or direct query
        # Note: Supabase Python client doesn't support direct SQL execution
        # We'll use the REST API directly
        print(f"   ⚠️  Aviso: Execute manualmente no Supabase Dashboard > SQL Editor")
        print(f"   Arquivo: {file_path}")
        return
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        raise

def check_tables_exist(client: Client) -> dict:
    """Check if required tables exist"""
    tables_status = {}
    
    # Check assistants table
    try:
        result = client.table('assistants').select('id').limit(1).execute()
        tables_status['assistants'] = len(result.data) if result.data else 0
    except Exception:
        tables_status['assistants'] = None
    
    # Check communication_styles table
    try:
        result = client.table('communication_styles').select('id').limit(1).execute()
        tables_status['communication_styles'] = len(result.data) if result.data else 0
    except Exception:
        tables_status['communication_styles'] = None
    
    # Check configurations table
    try:
        result = client.table('configurations').select('id').limit(1).execute()
        tables_status['configurations'] = len(result.data) if result.data else 0
    except Exception:
        tables_status['configurations'] = None
    
    return tables_status

def main():
    """Main initialization function"""
    print("🚀 Inicializando banco de dados...")
    print("=" * 60)
    
    try:
        client = get_supabase_client()
        print("✅ Conectado ao Supabase")
        
        # Check current state
        print("\n📊 Verificando estado atual...")
        tables = check_tables_exist(client)
        
        for table, count in tables.items():
            if count is None:
                print(f"   ❌ Tabela '{table}' não existe")
            else:
                print(f"   ✅ Tabela '{table}' existe ({count} registros)")
        
        # Check if initialization is needed
        needs_init = any(count is None or count == 0 for count in tables.values())
        
        if not needs_init:
            print("\n✅ Banco de dados já está inicializado!")
            return
        
        print("\n⚠️  ATENÇÃO: Algumas tabelas precisam ser criadas/populadas")
        print("\n📝 Execute a migration completa no Supabase Dashboard:")
        print("   1. Acesse: https://app.supabase.com/project/_/sql")
        print("   2. Cole o conteúdo de: backend/migrations/000_full_migration_assistants_communication_styles.sql")
        print("   3. Execute o script")
        print("\n💡 Ou use o script run_migration.py:")
        print("   python backend/run_migration.py backend/migrations/000_full_migration_assistants_communication_styles.sql")
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
